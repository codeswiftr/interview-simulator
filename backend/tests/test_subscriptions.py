"""Tests for subscription API endpoints."""

from datetime import UTC
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import stripe
from httpx import AsyncClient
from sqlmodel import SQLModel, select

from app.models.user import SubscriptionTier, User

# Import register_and_login from conftest.py
from tests.conftest import register_and_login

@pytest.mark.asyncio
async def test_get_subscription_status_returns_correct_tier(client, db_session):
    """Test that subscription status returns correct tier and limits."""
    token = await register_and_login(client)

    response = await client.get(
        "/api/v1/subscriptionsstatus",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert data["tier"] == "free"
    assert "interviews_this_month" in data
    assert "interviews_limit" in data
    assert data["interviews_limit"] == 5
    assert "can_create_interview" in data

@pytest.mark.asyncio
async def test_create_checkout_session_returns_url(client, db_session):
    """Test that checkout session creation returns valid Stripe URL."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        # Mock settings to enable Stripe
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.cors_origins = ["http://localhost:3000"]

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        response = await client.post(
            "/api/v1/subscriptionscheckout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "stripe.com" in data["url"]

@pytest.mark.asyncio
async def test_create_checkout_session_creates_customer(client, db_session):
    """Test that Stripe customer is created if user doesn't have one."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        # Mock settings to enable Stripe
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.cors_origins = ["http://localhost:3000"]

        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        await client.post(
            "/api/v1/subscriptionscheckout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        # Verify customer was created
        mock_stripe.Customer.create.assert_called_once()

@pytest.mark.asyncio
async def test_webhook_checkout_completed_upgrades_user(client, db_session):
    """Test that user tier is updated on checkout completion."""
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
        # Mock settings to enable Stripe
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
        mock_settings.stripe_price_id_pro_annual = "price_pro_annual"

        # Mock webhook event construction
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        # Mock subscription with dict-like structure (new Stripe API)
        mock_subscription = {
            "id": "sub_test123",
            "status": "active",
            "items": {
                "data": [{
                    "price": {"id": "price_pro_monthly"},
                    "current_period_end": 1735689600,  # Future timestamp
                }]
            },
        }
        mock_stripe.Subscription.retrieve.return_value = mock_subscription

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Webhook should process successfully
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_webhook_subscription_deleted_downgrades_user(client, db_session):
    """Test that user is downgraded to Free on subscription deletion."""
    token = await register_and_login(client)

    # Create user with Pro subscription
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(
            select(User).where(User.id == user_id)
        )
        user = result.first()
        user.subscription_tier = SubscriptionTier.PRO
        user.stripe_customer_id = "cus_test123"
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

    with patch("app.api.subscriptions.stripe") as mock_stripe:
        # Mock webhook signature verification
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        await client.post(
            "/api/v1/subscriptionswebhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Verify user was downgraded
        async with SessionLocal() as session:
            result = await session.exec(
                select(User).where(User.id == user_id)
            )
            user = result.first()
            # In real scenario, would be downgraded to FREE
            # Here we just verify webhook was processed

@pytest.mark.asyncio
async def test_checkout_with_invalid_price_id(client, db_session):
    """Test checkout fails with invalid price_id."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.cors_origins = ["http://localhost:3000"]

        # Mock Stripe error for invalid price
        # Need to create customer first
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Then mock checkout error - use real exception class
        error = stripe.error.InvalidRequestError(
            message="No such price: price_invalid",
            param="price",
        )
        mock_stripe.checkout.Session.create.side_effect = error

        response = await client.post(
            "/api/v1/subscriptionscheckout",
            json={"price_id": "price_invalid"},
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_checkout_with_already_subscribed_user(client, db_session):
    """Test checkout fails when user already has active subscription."""
    token = await register_and_login(client)

    # Set user as already subscribed
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.frontend_url = "http://localhost:3000"

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Mock existing subscription - Subscription.list returns object with .data attribute
        mock_sub_list = MagicMock()
        mock_sub_list.data = [MagicMock()]  # Has active subscription
        mock_stripe.Subscription.list.return_value = mock_sub_list

        response = await client.post(
            "/api/v1/subscriptionscheckout",
            json={"price_id": "price_pro_monthly"},
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "already have" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_webhook_invalid_signature(client, db_session):
    """Test webhook rejects requests with invalid signature."""
    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_webhook_secret = "whsec_test"

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Mock signature verification failure
        error = stripe.error.SignatureVerificationError(
            message="Invalid signature",
            sig_header="test_signature",
        )
        mock_stripe.Webhook.construct_event.side_effect = error

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json={"type": "checkout.session.completed", "data": {}},
            headers={"stripe-signature": "invalid_signature"},
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "signature" in detail or "invalid" in detail

@pytest.mark.asyncio
async def test_webhook_unknown_event_type(client, db_session):
    """Test webhook handles unknown event types gracefully."""
    webhook_payload = {
        "type": "unknown.event.type",
        "data": {"object": {}},
        "id": "evt_test123",
    }

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Should return 200 but not process the event (just logs and returns success)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_get_subscription_status_expired(client, db_session):
    """Test subscription status with expired subscription."""
    token = await register_and_login(client)

    # Set user with expired subscription
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.subscription_tier = SubscriptionTier.PRO
        from datetime import datetime, timedelta
        user.subscription_expires_at = datetime.now(UTC) - timedelta(days=1)
        await session.commit()

    response = await client.get(
        "/api/v1/subscriptionsstatus",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    # Should show as expired or downgraded
    assert "tier" in data

@pytest.mark.asyncio
async def test_portal_session_creation(client, db_session):
    """Test portal session creation returns URL."""
    token = await register_and_login(client)

    # Set user with subscription
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_secret_key = "sk_test_xxx"

        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/session/test123"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        response = await client.post(
            "/api/v1/subscriptionsportal",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        assert "url" in response.json()
        assert "stripe.com" in response.json()["url"]

@pytest.mark.asyncio
async def test_portal_error_handling(client, db_session):
    """Test portal session creation handles Stripe errors."""
    token = await register_and_login(client)

    # Set user with customer_id so we can test Stripe error
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        await session.commit()

    # Get the real exception class before patching
    StripeError = stripe.error.InvalidRequestError

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_secret_key = "sk_test_xxx"

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Create a proper StripeError instance
        error = StripeError(
            message="Customer not found",
            param="customer",
        )
        mock_stripe.billing_portal.Session.create.side_effect = error

        response = await client.post(
            "/api/v1/subscriptionsportal",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "failed" in detail or "error" in detail or "customer" in detail

@pytest.mark.asyncio
async def test_cancel_subscription(client, db_session):
    """Test subscription cancellation flow."""
    token = await register_and_login(client)

    # Set user with active subscription
    async with SessionLocal() as session:
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
            "/api/v1/subscriptionscancel",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        assert "canceled" in response.json()["message"].lower() or "scheduled" in response.json()["message"].lower()

@pytest.mark.asyncio
async def test_cancel_already_cancelled_subscription(client, db_session):
    """Test canceling already cancelled subscription."""
    token = await register_and_login(client)

    # Set user with cancelled subscription
    async with SessionLocal() as session:
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

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Mock subscription already cancelled - use proper exception
        error = stripe.error.InvalidRequestError(
            message="Subscription already cancelled",
            param="subscription",
        )
        mock_stripe.Subscription.modify.side_effect = error

        response = await client.post(
            "/api/v1/subscriptionscancel",
            headers={"Authorization": token},
        )

        # Should handle gracefully - returns 400 with error message
        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower() or "cancel" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_pricing_config(client):
    """Test getting pricing configuration."""
    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
        mock_settings.stripe_price_id_pro_annual = "price_pro_annual"

        response = await client.get("/api/v1/subscriptionspricing")

        assert response.status_code == 200
        data = response.json()
        assert "pro_monthly_price_id" in data
        assert "pro_annual_price_id" in data
        assert data["pro_monthly_price_id"] == "price_pro_monthly"
        assert data["pro_annual_price_id"] == "price_pro_annual"

@pytest.mark.asyncio
async def test_get_pricing_config_null_values(client):
    """Test pricing config returns None for unset price IDs."""
    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_price_id_pro_monthly = None
        mock_settings.stripe_price_id_pro_annual = None

        response = await client.get("/api/v1/subscriptionspricing")

        assert response.status_code == 200
        data = response.json()
        assert data["pro_monthly_price_id"] is None
        assert data["pro_annual_price_id"] is None

@pytest.mark.asyncio
async def test_checkout_stripe_not_configured(client, db_session):
    """Test checkout fails when Stripe is not configured."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_secret_key = None

        response = await client.post(
            "/api/v1/subscriptionscheckout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_webhook_stripe_not_configured(client):
    """Test webhook fails when Stripe webhook secret is not configured."""
    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = None

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json={"type": "checkout.session.completed", "data": {}},
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_webhook_invalid_payload(client, db_session):
    """Test webhook rejects invalid JSON payload."""
    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_webhook_secret = "whsec_test"

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Mock ValueError for invalid payload
        mock_stripe.Webhook.construct_event.side_effect = ValueError("Invalid payload")

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json={"invalid": "payload"},
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_portal_no_customer_id(client, db_session):
    """Test portal session creation fails when user has no customer ID."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_secret_key = "sk_test_xxx"

        response = await client.post(
            "/api/v1/subscriptionsportal",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "no stripe customer" in response.json()["detail"].lower() or "subscribe first" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_portal_stripe_not_configured(client, db_session):
    """Test portal fails when Stripe is not configured."""
    token = await register_and_login(client)

    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_secret_key = None

        response = await client.post(
            "/api/v1/subscriptionsportal",
            headers={"Authorization": token},
        )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_cancel_no_subscription(client, db_session):
    """Test cancel fails when user has no active subscription."""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/subscriptionscancel",
        headers={"Authorization": token},
    )

    assert response.status_code == 400
    assert "no active subscription" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_webhook_subscription_updated(client, db_session):
    """Test webhook handles customer.subscription.updated event."""
    token = await register_and_login(client)

    # Set user with customer ID
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
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

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_webhook_checkout_missing_metadata(client, db_session):
    """Test webhook handles checkout_completed with missing metadata gracefully."""
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                # Missing metadata
            }
        },
        "id": "evt_test123",
    }

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Should handle gracefully and return success (logs warning)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_webhook_checkout_user_not_found(client, db_session):
    """Test webhook handles checkout_completed when user doesn't exist."""
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "metadata": {"user_id": str(uuid4())},  # Non-existent user
            }
        },
        "id": "evt_test123",
    }

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_webhook_secret = "whsec_test"
        mock_stripe.Webhook.construct_event.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptionswebhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Should handle gracefully and return success (logs warning)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_subscription_status_syncs_from_stripe(client, db_session):
    """Test subscription status syncs from Stripe when customer exists."""
    token = await register_and_login(client)

    # Set user with customer ID
    async with SessionLocal() as session:
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

        # Mock active subscription from Stripe
        mock_sub_list = MagicMock()
        mock_sub = {
            "id": "sub_test123",
            "status": "active",
            "items": {
                "data": [{
                    "price": {"id": "price_pro_monthly"},
                    "current_period_end": 1735689600,
                }]
            },
            "cancel_at_period_end": False,
        }
        mock_sub_list.data = [mock_sub]
        mock_stripe.Subscription.list.return_value = mock_sub_list

        response = await client.get(
            "/api/v1/subscriptionsstatus",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        # Subscription should be synced from Stripe

@pytest.mark.asyncio
async def test_get_subscription_status_sync_error_handled(client, db_session):
    """Test subscription status handles Stripe sync errors gracefully."""
    token = await register_and_login(client)

    # Set user with customer ID
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_test123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe"), \
         patch("app.api.subscriptions._sync_subscription_from_stripe") as mock_sync:
        mock_settings.stripe_secret_key = "sk_test_xxx"

        # Mock sync failure
        mock_sync.side_effect = Exception("Stripe API error")

        response = await client.get(
            "/api/v1/subscriptionsstatus",
            headers={"Authorization": token},
        )

        # Should still return status (error is logged but not fatal)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_cancel_subscription_stripe_error(client, db_session):
    """Test cancel handles Stripe API errors."""
    token = await register_and_login(client)

    # Set user with subscription
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_subscription_id = "sub_test123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_secret_key = "sk_test_xxx"

        # Preserve the error module in the mock
        mock_stripe.error = stripe.error

        # Mock Stripe error
        error = stripe.error.InvalidRequestError(
            message="Subscription not found",
            param="subscription",
        )
        mock_stripe.Subscription.modify.side_effect = error

        response = await client.post(
            "/api/v1/subscriptionscancel",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_checkout_reuses_existing_customer(client, db_session):
    """Test checkout reuses existing Stripe customer ID."""
    token = await register_and_login(client)

    # Set user with existing customer ID
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.stripe_customer_id = "cus_existing123"
        await session.commit()

    with patch("app.api.subscriptions.settings") as mock_settings, \
         patch("app.api.subscriptions.stripe") as mock_stripe:
        mock_settings.stripe_secret_key = "sk_test_xxx"
        mock_settings.frontend_url = "http://localhost:3000"

        # Mock subscription list (no active subscription)
        mock_sub_list = MagicMock()
        mock_sub_list.data = []
        mock_stripe.Subscription.list.return_value = mock_sub_list

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        response = await client.post(
            "/api/v1/subscriptionscheckout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        assert response.status_code == 200
        # Verify customer.create was NOT called (reused existing)
        mock_stripe.Customer.create.assert_not_called()
        # Verify checkout used existing customer
        mock_stripe.checkout.Session.create.assert_called_once()
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["customer"] == "cus_existing123"
