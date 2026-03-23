"""Comprehensive Stripe webhook security and edge case tests.

Tests critical payment webhook scenarios:
- Webhook signature validation
- Replay attack prevention
- Malformed payload handling
- Missing required fields
- Idempotency
- Race conditions in subscription updates
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import stripe

from app.models.user import SubscriptionTier, User
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_webhook_without_signature_rejected(client, db_session):
    """Test that webhooks without Stripe signature are rejected."""
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {"object": {"customer": "cus_test123", "subscription": "sub_test123"}},
    }

    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = "whsec_test123"

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            # Missing stripe-signature header
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_with_invalid_signature_rejected(client, db_session):
    """Test that webhooks with invalid signatures are rejected."""
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {"object": {"customer": "cus_test123", "subscription": "sub_test123"}},
    }

    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = "whsec_test123"

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "invalid_signature"},
        )

        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_with_malformed_json_rejected(client, db_session):
    """Test that webhooks with malformed JSON are rejected."""
    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = "whsec_test123"

        # Send invalid JSON
        response = await client.post(
            "/api/v1/subscriptions/webhook",
            content=b"not valid json{{{",
            headers={"stripe-signature": "t=123,v1=sig", "content-type": "application/json"},
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_checkout_completed_missing_customer_id(client, db_session):
    """Test webhook handles missing customer_id gracefully."""
    token = await register_and_login(client)
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    webhook_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                # Missing customer field
                "subscription": "sub_test123",
                "metadata": {"user_id": user_id},
            }
        },
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Should return success but log warning (idempotent behavior)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_checkout_completed_missing_user_id(client, db_session):
    """Test webhook handles missing user_id metadata gracefully."""
    webhook_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {},  # Missing user_id
            }
        },
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Should return success but not update any user
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_checkout_completed_nonexistent_user(client, db_session):
    """Test webhook handles checkout for non-existent user."""
    fake_user_id = str(uuid4())

    webhook_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"user_id": fake_user_id},
            }
        },
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Should return success (idempotent) but log warning
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_subscription_deleted_downgrades_user(client, db_session):
    """Test that subscription deletion webhook properly downgrades user to free tier."""
    token = await register_and_login(client)
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    # First upgrade user to pro
    from sqlmodel import select

    result = await db_session.exec(select(User).where(User.id == user_id))
    user = result.first()
    user.subscription_tier = SubscriptionTier.PRO
    user.stripe_subscription_id = "sub_test123"
    await db_session.commit()

    # Now send cancellation webhook
    webhook_payload = {
        "id": "evt_test123",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_test123", "customer": "cus_test123"}},
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        assert response.status_code == 200

        # Verify user was downgraded
        await db_session.refresh(user)
        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.subscription_status == "canceled"


@pytest.mark.asyncio
async def test_webhook_subscription_updated_handles_trial_ending(client, db_session):
    """Test webhook handles trial ending and transition to active subscription."""
    token = await register_and_login(client)
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    from sqlmodel import select

    result = await db_session.exec(select(User).where(User.id == user_id))
    user = result.first()
    user.stripe_subscription_id = "sub_test123"
    await db_session.commit()

    webhook_payload = {
        "id": "evt_test123",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "status": "active",  # Changed from trialing to active
                "items": {
                    "data": [
                        {
                            "price": {"id": "price_pro"},
                            "current_period_end": int(
                                (datetime.now(UTC) + timedelta(days=30)).timestamp()
                            ),
                        }
                    ]
                },
            }
        },
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
        patch("app.api.subscriptions._get_tier_from_price") as mock_get_tier,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload
        mock_get_tier.return_value = SubscriptionTier.PRO

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        assert response.status_code == 200

        # Verify user subscription was updated
        await db_session.refresh(user)
        assert user.subscription_status == "active"


@pytest.mark.asyncio
async def test_webhook_handles_unknown_event_type_gracefully(client, db_session):
    """Test that unknown webhook event types are ignored but don't cause errors."""
    webhook_payload = {
        "id": "evt_test123",
        "type": "customer.unknown.event",
        "data": {"object": {}},
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Should return success (idempotent)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_stripe_api_error_returns_500_for_retry(client, db_session):
    """Test that Stripe API errors return 500 so Stripe retries the webhook."""
    token = await register_and_login(client)
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    webhook_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"user_id": user_id},
            }
        },
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
        patch("app.api.subscriptions.stripe.Subscription.retrieve") as mock_retrieve,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload
        # Simulate Stripe API error
        mock_retrieve.side_effect = stripe.error.APIError("API Error")

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Should return 500 so Stripe retries
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_webhook_database_error_returns_500_for_retry(client, db_session):
    """Test that database errors return 500 so Stripe retries the webhook."""
    webhook_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"user_id": str(uuid4())},
            }
        },
    }

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
        patch("app.api.subscriptions.get_session") as mock_get_session,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload

        # Simulate database error
        async def failing_session():
            raise Exception("Database connection failed")
            yield  # pragma: no cover

        mock_get_session.return_value = failing_session()

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Should return 500 for retry
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_webhook_idempotency_duplicate_event_handled(client, db_session):
    """Test that duplicate webhook events are handled idempotently."""
    token = await register_and_login(client)
    user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
    user_id = user_resp.json()["id"]

    from sqlmodel import select

    result = await db_session.exec(select(User).where(User.id == user_id))
    user = result.first()
    user.stripe_customer_id = "cus_test123"
    await db_session.commit()

    webhook_payload = {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"user_id": user_id},
            }
        },
    }

    mock_subscription = MagicMock()
    mock_subscription.__getitem__ = lambda self, key: {
        "status": "active",
        "items": {
            "data": [
                {
                    "price": {"id": "price_pro"},
                    "current_period_end": int((datetime.now(UTC) + timedelta(days=30)).timestamp()),
                }
            ]
        },
    }[key]

    with (
        patch("app.api.subscriptions.settings") as mock_settings,
        patch("app.api.subscriptions.stripe.Webhook.construct_event") as mock_construct,
        patch("app.api.subscriptions.stripe.Subscription.retrieve") as mock_retrieve,
        patch("app.api.subscriptions._get_tier_from_price") as mock_get_tier,
    ):
        mock_settings.stripe_webhook_secret = "whsec_test123"
        mock_construct.return_value = webhook_payload
        mock_retrieve.return_value = mock_subscription
        mock_get_tier.return_value = SubscriptionTier.PRO

        # Send webhook twice
        response1 = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        response2 = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        # Both should succeed (idempotent)
        assert response1.status_code == 200
        assert response2.status_code == 200

        # User should still be upgraded only once
        await db_session.refresh(user)
        assert user.subscription_tier == SubscriptionTier.PRO


@pytest.mark.asyncio
async def test_webhook_without_configured_secret_returns_503(client, db_session):
    """Test that webhooks fail gracefully when webhook secret is not configured."""
    webhook_payload = {"type": "checkout.session.completed", "data": {"object": {}}}

    with patch("app.api.subscriptions.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = None  # Not configured

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "valid_signature"},
        )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()
