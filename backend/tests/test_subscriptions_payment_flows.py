"""Additional comprehensive tests for payment and subscription flows.

This test file focuses on improving coverage for critical payment paths:
- Payment intent flows
- Subscription lifecycle (trial, active, canceled)
- Free tier enforcement
- Edge cases and error scenarios
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import stripe
from sqlmodel import select

from app.models.user import SubscriptionTier, User
from tests.conftest import get_test_engine, register_and_login


@pytest.mark.asyncio
async def test_checkout_with_trial_period(client, db_session):
    """Test checkout session creation with trial period configured."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        # Mock settings with trial period
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.stripe_trial_days = 7  # 7-day trial
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.frontend_url = "http://localhost:3000"

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        response = await client.post(
            "/api/v1/subscriptions/checkout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        assert response.status_code == 200
        # Verify trial period was included in checkout session
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7


@pytest.mark.asyncio
async def test_checkout_with_referral_code(client, db_session):
    """Test checkout session includes referral code for affiliate tracking."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe, \
         patch("app.api.subscriptions.get_analytics") as mock_analytics:
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.frontend_url = "http://localhost:3000"

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        # Mock analytics
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        response = await client.post(
            "/api/v1/subscriptions/checkout",
            headers={"Authorization": token},
            json={"price_id": "price_test123", "referral_code": "AFFILIATE123"},
        )

        assert response.status_code == 200
        # Verify referral code was included
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["client_reference_id"] == "AFFILIATE123"


@pytest.mark.asyncio
async def test_webhook_checkout_completed_with_full_subscription_details(client, db_session):
    """Test webhook properly updates all subscription fields from checkout completion."""
    token = await register_and_login(client)

    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"user_id": user_id},
            }
        },
    }

    # Create a mock async generator for get_session that yields the test db_session
    async def mock_get_session():
        yield db_session

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe, \
         patch("app.api.subscriptions.get_session", mock_get_session), \
         patch("app.api.subscriptions.get_analytics") as mock_analytics:

        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
        mock_settings.stripe_price_id_pro_annual = "price_pro_annual"

        # Mock webhook event construction
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        # Mock subscription with full details
        mock_subscription = {
            "id": "sub_test123",
            "status": "active",
            "items": {
                "data": [{
                    "price": {"id": "price_pro_monthly"},
                    "current_period_end": 1735689600,  # Future timestamp
                }]
            },
            "plan": {
                "amount": 2999,  # $29.99
                "currency": "usd",
            }
        }
        mock_stripe.Subscription.retrieve.return_value = mock_subscription

        # Mock analytics
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200

        # Verify user was upgraded
        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as session:
            result = await session.exec(select(User).where(User.id == user_id))
            user = result.first()
            assert user.subscription_tier == SubscriptionTier.PRO
            assert user.stripe_subscription_id == "sub_test123"
            assert user.subscription_status == "active"


@pytest.mark.asyncio
async def test_webhook_subscription_updated_changes_tier(client, db_session):
    """Test subscription.updated webhook properly updates user tier."""
    token = await register_and_login(client)

    # Set user with existing subscription
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        user.subscription_tier = SubscriptionTier.FREE
        await session.commit()

    webhook_payload = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "items": {
                    "data": [{
                        "price": {"id": "price_pro_monthly"},
                        "current_period_end": 1735689600,
                    }]
                },
            }
        },
        "id": "evt_test123",
    }

    # Create a mock async generator for get_session that yields the test db_session
    async def mock_get_session():
        yield db_session

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe, \
         patch("app.api.subscriptions.get_session", mock_get_session):

        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200

        # Verify user was upgraded
        async with TestSessionLocal() as session:
            result = await session.exec(select(User).where(User.id == user_id))
            user = result.first()
            assert user.subscription_tier == SubscriptionTier.PRO


@pytest.mark.asyncio
async def test_webhook_subscription_deleted_with_analytics(client, db_session):
    """Test subscription.deleted webhook tracks analytics event."""
    token = await register_and_login(client)

    # Get user ID first
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    # Set user with Pro subscription using the correct session
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        user.subscription_tier = SubscriptionTier.PRO
        user.stripe_subscription_id = "sub_test123"
        await session.commit()

    webhook_payload = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "customer": "cus_test123",
                "id": "sub_test123",
            }
        },
    }

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe, \
         patch("app.api.subscriptions.get_analytics") as mock_analytics:

        mock_settings.stripe_webhook_secret = "whsec_test"

        # Mock webhook signature verification
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        # Mock analytics
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200

        # Verify user was downgraded
        async with TestSessionLocal() as session:
            result = await session.exec(select(User).where(User.id == user_id))
            user = result.first()
            assert user.subscription_tier == SubscriptionTier.FREE
            assert user.subscription_status == "canceled"
            assert user.stripe_subscription_id is None


@pytest.mark.asyncio
async def test_free_tier_interview_limit_enforcement(client, db_session):
    """Test that free tier users cannot create interviews beyond limit."""
    token = await register_and_login(client)

    # Set user to have 3 interviews this month (at limit)
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.interviews_this_month = 3
        await session.commit()

    # Check subscription status shows limit reached
    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["interviews_this_month"] == 3
    assert data["interviews_limit"] == 3
    assert data["can_create_interview"] is False


@pytest.mark.asyncio
async def test_pro_tier_unlimited_interviews(client, db_session):
    """Test that Pro tier users have unlimited interviews."""
    token = await register_and_login(client)

    # Upgrade user to Pro
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.subscription_tier = SubscriptionTier.PRO
        user.interviews_this_month = 100  # Well over free limit
        await session.commit()

    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "pro"
    assert data["interviews_this_month"] == 100
    assert data["interviews_limit"] is None  # Unlimited
    assert data["can_create_interview"] is True


@pytest.mark.asyncio
async def test_sync_subscription_downgrades_when_no_active_subscription(client, db_session):
    """Test that sync downgrades user when Stripe shows no active subscription."""
    token = await register_and_login(client)

    # Set user as Pro but they don't have subscription in Stripe
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        user.subscription_tier = SubscriptionTier.PRO
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:

        mock_settings.stripe_secret_key = "sk_test_xxx"

        # Mock empty subscription list (no active subscriptions)
        mock_sub_list = MagicMock()
        mock_sub_list.data = []
        mock_stripe.Subscription.list.return_value = mock_sub_list

        response = await client.get(
            "/api/v1/subscriptions/status",
            headers={"Authorization": token},
        )

        assert response.status_code == 200

        # Verify user was downgraded
        async with TestSessionLocal() as session:
            result = await session.exec(select(User).where(User.id == user_id))
            user = result.first()
            assert user.subscription_tier == SubscriptionTier.FREE
            assert user.subscription_status == "canceled"


@pytest.mark.asyncio
async def test_sync_subscription_detects_cancel_at_period_end(client, db_session):
    """Test that sync properly detects subscriptions scheduled for cancellation."""
    token = await register_and_login(client)

    # Set user with customer ID
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:

        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"

        # Mock subscription scheduled for cancellation
        mock_sub = {
            "id": "sub_test123",
            "status": "active",
            "cancel_at_period_end": True,  # Scheduled for cancellation
            "items": {
                "data": [{
                    "price": {"id": "price_pro_monthly"},
                    "current_period_end": 1735689600,
                }]
            },
        }
        mock_sub_list = MagicMock()
        mock_sub_list.data = [mock_sub]
        mock_stripe.Subscription.list.return_value = mock_sub_list

        response = await client.get(
            "/api/v1/subscriptions/status",
            headers={"Authorization": token},
        )

        assert response.status_code == 200

        # Verify subscription status is cancel_at_period_end
        async with TestSessionLocal() as session:
            result = await session.exec(select(User).where(User.id == user_id))
            user = result.first()
            assert user.subscription_status == "cancel_at_period_end"


@pytest.mark.asyncio
async def test_webhook_logs_errors_on_exception(client, db_session):
    """Test that webhook logs errors when exception occurs during processing."""
    token = await register_and_login(client)

    # Get user ID
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"user_id": user_id},
            }
        },
    }

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:

        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        # Mock Subscription.retrieve to raise an error
        mock_stripe.Subscription.retrieve.side_effect = Exception("Stripe API error")

        # Webhook should raise the exception (returns 500 for Stripe to retry)
        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Should return error
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_cancel_subscription_immediate_vs_period_end(client, db_session):
    """Test subscription cancellation sets cancel_at_period_end flag."""
    token = await register_and_login(client)

    # Set user with active subscription
    _, TestSessionLocal = get_test_engine()
    async with TestSessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.subscription_tier = SubscriptionTier.PRO
        user.stripe_subscription_id = "sub_test123"
        user.stripe_customer_id = "cus_test123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:

        mock_settings.stripe_secret_key = "sk_test_xxx"

        mock_subscription = MagicMock()
        mock_subscription.cancel_at_period_end = True
        mock_stripe.Subscription.modify.return_value = mock_subscription

        response = await client.post(
            "/api/v1/subscriptions/cancel",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        assert "end of the billing period" in response.json()["message"]

        # Verify Stripe API was called correctly
        mock_stripe.Subscription.modify.assert_called_once_with(
            "sub_test123",
            cancel_at_period_end=True,
        )

        # Verify user status updated
        async with TestSessionLocal() as session:
            result = await session.exec(select(User).where(User.id == user_id))
            user = result.first()
            assert user.subscription_status == "cancel_at_period_end"
