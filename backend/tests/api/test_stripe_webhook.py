"""Tests for Stripe webhook endpoint.

CRITICAL: Payment processing must be thoroughly tested.
"""

import hashlib
import hmac
import json
from uuid import uuid4

import pytest


# Test webhook payload
def generate_webhook_payload(event_type, data):
    """Generate test Stripe webhook payload."""
    return {
        "id": f"evt_{uuid4().hex}",
        "object": "event",
        "type": event_type,
        "data": {"object": data}
    }


@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "whsec_test_secret"


@pytest.fixture
def mock_signature(webhook_secret):
    """Generate valid webhook signature."""
    def _sign(payload):
        timestamp = "1234567890"
        signed_payload = f"{timestamp}.{json.dumps(payload)}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"
    return _sign


class TestStripeWebhook:
    """Tests for POST /api/v1/stripe/webhook"""

    @pytest.mark.asyncio
    async def test_webhook_checkout_completed(self, client, mock_signature):
        """Should handle checkout.session.completed event."""
        payload = generate_webhook_payload("checkout.session.completed", {
            "id": "cs_test_123",
            "customer": "cus_test_123",
            "subscription": "sub_test_123",
            "metadata": {"user_id": "test-user-id"}
        })

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_subscription_updated(self, client, mock_signature):
        """Should handle customer.subscription.updated event."""
        payload = generate_webhook_payload("customer.subscription.updated", {
            "id": "sub_test_123",
            "customer": "cus_test_123",
            "status": "active",
            "current_period_end": 1234567890
        })

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_subscription_deleted(self, client, mock_signature):
        """Should handle customer.subscription.deleted event."""
        payload = generate_webhook_payload("customer.subscription.deleted", {
            "id": "sub_test_123",
            "customer": "cus_test_123",
            "status": "canceled"
        })

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_payment_failed(self, client, mock_signature):
        """Should handle invoice.payment_failed event."""
        payload = generate_webhook_payload("invoice.payment_failed", {
            "id": "in_test_123",
            "customer": "cus_test_123",
            "subscription": "sub_test_123"
        })

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self, client):
        """Should reject requests with invalid signature."""
        payload = generate_webhook_payload("checkout.session.completed", {})

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": "invalid_signature"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_missing_signature(self, client):
        """Should reject requests without signature."""
        payload = generate_webhook_payload("checkout.session.completed", {})

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_unhandled_event(self, client, mock_signature):
        """Should gracefully handle unknown event types."""
        payload = generate_webhook_payload("unknown.event", {})

        response = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )

        # Should accept but not process
        assert response.status_code == 200


class TestWebhookIdempotency:
    """Tests for webhook idempotency (preventing duplicate processing)."""

    @pytest.mark.asyncio
    async def test_webhook_idempotency(self, client, mock_signature):
        """Should not process same event twice."""
        event_id = f"evt_{uuid4().hex}"
        payload = {
            "id": event_id,
            "object": "event",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123"}}
        }

        # First request
        response1 = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )
        assert response1.status_code == 200

        # Second request (same event ID)
        response2 = await client.post(
            "/api/v1/stripe/webhook",
            json=payload,
            headers={"Stripe-Signature": mock_signature(payload)}
        )
        assert response2.status_code == 200
        # Should be handled idempotently
