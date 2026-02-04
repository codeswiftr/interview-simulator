"""Tests for subscription/payment endpoints.

Critical: These tests cover revenue-related functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


@pytest.fixture
def mock_stripe():
    """Mock Stripe client for testing."""
    with patch("app.api.subscriptions.stripe") as mock:
        # Mock checkout session
        mock.checkout.Session.create = MagicMock(return_value=MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test"
        ))
        # Mock billing portal
        mock.billing_portal.Session.create = MagicMock(return_value=MagicMock(
            url="https://billing.stripe.com/test"
        ))
        yield mock


class TestCheckoutSession:
    """Tests for POST /api/v1/subscriptions/checkout"""

    @pytest.mark.asyncio
    async def test_create_checkout_success(self, client, auth_headers, mock_stripe):
        """Should create checkout session successfully."""
        response = await client.post(
            "/api/v1/subscriptions/checkout",
            json={"price_id": "price_123", "tier": "pro"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert data["session_id"] == "cs_test_123"
        mock_stripe.checkout.Session.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkout_unauthenticated(self, client):
        """Should reject unauthenticated requests."""
        response = await client.post(
            "/api/v1/subscriptions/checkout",
            json={"price_id": "price_123", "tier": "pro"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_price(self, client, auth_headers, mock_stripe):
        """Should handle Stripe errors gracefully."""
        mock_stripe.checkout.Session.create.side_effect = Exception("Invalid price")
        
        response = await client.post(
            "/api/v1/subscriptions/checkout",
            json={"price_id": "invalid", "tier": "pro"},
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestSubscriptionStatus:
    """Tests for GET /api/v1/subscriptions/status"""

    @pytest.mark.asyncio
    async def test_get_subscription_status(self, client, auth_headers):
        """Should return current subscription status."""
        response = await client.get(
            "/api/v1/subscriptions/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tier" in data
        assert "status" in data
        assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_get_subscription_free_tier(self, client, auth_headers):
        """Should return free tier for new users."""
        response = await client.get(
            "/api/v1/subscriptions/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"


class TestBillingPortal:
    """Tests for POST /api/v1/subscriptions/portal"""

    @pytest.mark.asyncio
    async def test_create_portal_session(self, client, auth_headers, mock_stripe):
        """Should create billing portal session."""
        response = await client.post(
            "/api/v1/subscriptions/portal",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "portal_url" in data
        mock_stripe.billing_portal.Session.create.assert_called_once()


class TestPricingConfig:
    """Tests for GET /api/v1/subscriptions/pricing"""

    @pytest.mark.asyncio
    async def test_get_pricing(self, client):
        """Should return pricing configuration."""
        response = await client.get("/api/v1/subscriptions/pricing")
        
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) > 0
        
        # Check plan structure
        plan = data["plans"][0]
        assert "id" in plan
        assert "name" in plan
        assert "price_monthly" in plan
        assert "features" in plan


class TestCancelSubscription:
    """Tests for POST /api/v1/subscriptions/cancel"""

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, client, auth_headers, mock_stripe):
        """Should cancel subscription at period end."""
        response = await client.post(
            "/api/v1/subscriptions/cancel",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancellation_scheduled"

    @pytest.mark.asyncio
    async def test_cancel_free_tier(self, client, auth_headers):
        """Should handle cancel on free tier gracefully."""
        response = await client.post(
            "/api/v1/subscriptions/cancel",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400]
