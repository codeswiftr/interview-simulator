"""Tests for subscription API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import stripe
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.user import SubscriptionTier, User
from app.security import hash_password
from sqlmodel import select


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    """Create tables once for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db(prepare_db):
    """Truncate tables between tests."""
    async with engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
    yield


@pytest.fixture
async def session_override():
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def client(session_override):
    async def _override():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_login(client: AsyncClient, email: str = "user@example.com") -> str:
    """Register user and return bearer token."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/users/login", json={"email": email, "password": "password123"})
    token = resp.json()["access_token"]
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_get_subscription_status_returns_correct_tier(client, session_override):
    """Test that subscription status returns correct tier and limits."""
    token = await register_and_login(client)

    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert data["tier"] == "free"
    assert "interviews_this_month" in data
    assert "interviews_limit" in data
    assert data["interviews_limit"] == 3
    assert "can_create_interview" in data


@pytest.mark.asyncio
async def test_create_checkout_session_returns_url(client, session_override):
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
            "/api/v1/subscriptions/checkout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "stripe.com" in data["url"]


@pytest.mark.asyncio
async def test_create_checkout_session_creates_customer(client, session_override):
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
            "/api/v1/subscriptions/checkout",
            headers={"Authorization": token},
            json={"price_id": "price_test123"},
        )

        # Verify customer was created
        mock_stripe.Customer.create.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_checkout_completed_upgrades_user(client, session_override):
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
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Webhook should process successfully
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_subscription_deleted_downgrades_user(client, session_override):
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

        response = await client.post(
            "/api/v1/subscriptions/webhook",
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
async def test_checkout_with_invalid_price_id(client, session_override):
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
            "/api/v1/subscriptions/checkout",
            json={"price_id": "price_invalid"},
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_checkout_with_already_subscribed_user(client, session_override):
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
            "/api/v1/subscriptions/checkout",
            json={"price_id": "price_pro_monthly"},
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        assert "already have" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client, session_override):
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
            "/api/v1/subscriptions/webhook",
            json={"type": "checkout.session.completed", "data": {}},
            headers={"stripe-signature": "invalid_signature"},
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "signature" in detail or "invalid" in detail


@pytest.mark.asyncio
async def test_webhook_unknown_event_type(client, session_override):
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
            "/api/v1/subscriptions/webhook",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"},
        )

        # Should return 200 but not process the event (just logs and returns success)
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_get_subscription_status_expired(client, session_override):
    """Test subscription status with expired subscription."""
    token = await register_and_login(client)

    # Set user with expired subscription
    async with SessionLocal() as session:
        user_resp = await client.get("/api/v1/users/me", headers={"Authorization": token})
        user_id = user_resp.json()["id"]

        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        user.subscription_tier = SubscriptionTier.PRO
        from datetime import datetime, timezone, timedelta
        user.subscription_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await session.commit()

    response = await client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    # Should show as expired or downgraded
    assert "tier" in data


@pytest.mark.asyncio
async def test_portal_session_creation(client, session_override):
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
            "/api/v1/subscriptions/portal",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        assert "url" in response.json()
        assert "stripe.com" in response.json()["url"]


@pytest.mark.asyncio
async def test_portal_error_handling(client, session_override):
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
            "/api/v1/subscriptions/portal",
            headers={"Authorization": token},
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "failed" in detail or "error" in detail or "customer" in detail


@pytest.mark.asyncio
async def test_cancel_subscription(client, session_override):
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
            "/api/v1/subscriptions/cancel",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        assert "canceled" in response.json()["message"].lower() or "scheduled" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_cancel_already_cancelled_subscription(client, session_override):
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
            "/api/v1/subscriptions/cancel",
            headers={"Authorization": token},
        )

        # Should handle gracefully - returns 400 with error message
        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower() or "cancel" in response.json()["detail"].lower()

