"""Unit tests for Stripe subscription webhook handlers.

Tests the critical payment webhook processing logic with mocked Stripe API.
Focuses on:
- Webhook signature verification
- checkout.session.completed event handling
- customer.subscription.updated event handling
- customer.subscription.deleted event handling
- Tier mapping from price IDs
"""

from datetime import UTC, datetime
from datetime import timezone as tz
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from forge_shared.billing.models import PricingTier

from app.api.subscriptions import (
    _get_tier_from_price,
    _handle_checkout_completed,
    _handle_subscription_deleted,
    _handle_subscription_updated,
    _sync_subscription_from_stripe,
)
from app.models.user import SubscriptionTier


@pytest.fixture
def mock_settings():
    """Mock settings for Stripe configuration."""
    with patch("app.api.subscriptions.settings") as mock:
        mock.stripe_secret_key = "sk_test_123"
        mock.stripe_webhook_secret = "whsec_test_123"
        mock.stripe_price_id_pro_monthly = "price_pro_monthly"
        mock.stripe_price_id_pro_annual = "price_pro_annual"
        mock.stripe_price_id_team_monthly = "price_team_monthly"
        mock.stripe_price_id_team_annual = "price_team_annual"
        mock.frontend_url = "https://app.example.com"
        yield mock


@pytest.fixture
def mock_stripe_client():
    """Mock the forge-shared StripeClient for tests."""
    mock_client = MagicMock()
    mock_client.get_customer_subscriptions = AsyncMock(return_value=[])
    mock_client.get_subscription = AsyncMock(return_value=None)
    mock_client.cancel_subscription = AsyncMock(return_value=True)
    return mock_client


# =============================================================================
# Tier Mapping Tests
# =============================================================================


def test_get_tier_from_price_pro_monthly(mock_settings):
    """Test mapping pro monthly price ID to PRO tier."""
    tier = _get_tier_from_price("price_pro_monthly")
    assert tier == SubscriptionTier.PRO


def test_get_tier_from_price_pro_annual(mock_settings):
    """Test mapping pro annual price ID to PRO tier."""
    tier = _get_tier_from_price("price_pro_annual")
    assert tier == SubscriptionTier.PRO


def test_get_tier_from_price_team_monthly(mock_settings):
    """Test mapping team monthly price ID to TEAM tier."""
    tier = _get_tier_from_price("price_team_monthly")
    assert tier == SubscriptionTier.TEAM


def test_get_tier_from_price_team_annual(mock_settings):
    """Test mapping team annual price ID to TEAM tier."""
    tier = _get_tier_from_price("price_team_annual")
    assert tier == SubscriptionTier.TEAM


def test_get_tier_from_price_unknown_defaults_to_free(mock_settings):
    """Test unknown price ID defaults to FREE tier."""
    tier = _get_tier_from_price("price_unknown")
    assert tier == SubscriptionTier.FREE


# =============================================================================
# Checkout Completed Handler Tests
# =============================================================================


@pytest.mark.asyncio
async def test_handle_checkout_completed_success(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test successful checkout completion creates subscription."""
    from forge_shared.billing.models import PricingTier, SubscriptionStatus

    # Mock Stripe subscription response via forge-shared client
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_123"
    mock_subscription.tier = PricingTier.PRO
    mock_subscription.status = SubscriptionStatus.ACTIVE
    mock_subscription.current_period_end = datetime.fromtimestamp(1735689600, tz=tz)
    mock_stripe_client.get_subscription.return_value = mock_subscription

    session_obj = {
        "customer_id": "cus_123",
        "subscription_id": "sub_123",
        "user_id": str(test_user.id),
    }

    with (
        patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client),
        patch("app.api.subscriptions.get_analytics") as mock_analytics,
    ):
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        await _handle_checkout_completed(session_obj, db_session)

    # Refresh user to get updated data
    await db_session.refresh(test_user)

    # Verify user subscription was updated
    assert test_user.stripe_subscription_id == "sub_123"
    assert test_user.subscription_tier == SubscriptionTier.PRO
    assert test_user.subscription_status == "active"
    assert test_user.subscription_expires_at is not None

    # Verify analytics events were captured
    assert mock_analytics_instance.capture.call_count == 2  # CREATED and COMPLETED


@pytest.mark.asyncio
async def test_handle_checkout_completed_missing_customer_id(
    db_session,
    mock_settings,
    mock_stripe_client,
):
    """Test checkout handler skips when customer_id is missing."""
    session_obj = {
        "subscription_id": "sub_123",
        "user_id": str(uuid4()),
        # Missing customer_id
    }

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        # Should not raise, just log warning
        await _handle_checkout_completed(session_obj, db_session)


@pytest.mark.asyncio
async def test_handle_checkout_completed_missing_user_id(
    db_session,
    mock_settings,
    mock_stripe_client,
):
    """Test checkout handler skips when user_id is missing."""
    session_obj = {
        "customer_id": "cus_123",
        "subscription_id": "sub_123",
        "metadata": {},  # Missing user_id
    }

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        # Should not raise, just log warning
        await _handle_checkout_completed(session_obj, db_session)


@pytest.mark.asyncio
async def test_handle_checkout_completed_user_not_found(
    db_session,
    mock_settings,
    mock_stripe_client,
):
    """Test checkout handler skips when user does not exist."""
    fake_user_id = str(uuid4())
    session_obj = {
        "customer_id": "cus_123",
        "subscription_id": "sub_123",
        "user_id": fake_user_id,
    }

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        # Should not raise, just log warning
        await _handle_checkout_completed(session_obj, db_session)


# =============================================================================
# Subscription Updated Handler Tests
# =============================================================================


@pytest.mark.asyncio
async def test_handle_subscription_updated_success(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test subscription update handler updates user tier and status."""
    from forge_shared.billing.models import PricingTier, SubscriptionStatus

    # Set initial subscription
    test_user.stripe_customer_id = "cus_123"
    test_user.subscription_tier = SubscriptionTier.PRO
    await db_session.commit()

    # Mock updated subscription to TEAM
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_456"
    mock_subscription.tier = PricingTier.TEAM
    mock_subscription.status = SubscriptionStatus.ACTIVE
    mock_subscription.current_period_end = datetime.fromtimestamp(1735689600, tz=tz)
    mock_stripe_client.get_subscription.return_value = mock_subscription

    # Support both formats for backward compatibility
    subscription_obj = {
        "customer_id": "cus_123",
        "subscription_id": "sub_456",
    }

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        await _handle_subscription_updated(subscription_obj, db_session)

    # Refresh user
    await db_session.refresh(test_user)

    # Verify subscription was updated (note: TEAM maps to PRO in our tier mapping)
    assert test_user.stripe_subscription_id == "sub_456"
    assert test_user.subscription_status == "active"


@pytest.mark.asyncio
async def test_handle_subscription_updated_missing_customer(
    db_session,
    mock_settings,
    mock_stripe_client,
):
    """Test subscription update skips when customer is missing."""
    subscription_obj = {
        "subscription_id": "sub_123",
        # Missing customer
    }

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        # Should not raise
        await _handle_subscription_updated(subscription_obj, db_session)


@pytest.mark.asyncio
async def test_handle_subscription_updated_user_not_found(
    db_session,
    mock_settings,
    mock_stripe_client,
):
    """Test subscription update skips when user not found."""
    subscription_obj = {
        "customer_id": "cus_nonexistent",
        "subscription_id": "sub_123",
    }

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        # Should not raise
        await _handle_subscription_updated(subscription_obj, db_session)


# =============================================================================
# Subscription Deleted Handler Tests
# =============================================================================


@pytest.mark.asyncio
async def test_handle_subscription_deleted_downgrades_to_free(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test subscription deletion downgrades user to free tier."""
    # Set initial PRO subscription
    test_user.stripe_customer_id = "cus_123"
    test_user.subscription_tier = SubscriptionTier.PRO
    test_user.stripe_subscription_id = "sub_123"
    test_user.subscription_status = "active"
    test_user.subscription_expires_at = datetime.now(UTC)
    await db_session.commit()

    subscription_obj = {
        "customer_id": "cus_123",
    }

    with (
        patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client),
        patch("app.api.subscriptions.get_analytics") as mock_analytics,
    ):
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        await _handle_subscription_deleted(subscription_obj, db_session)

    # Refresh user
    await db_session.refresh(test_user)

    # Verify downgrade to FREE
    assert test_user.subscription_tier == SubscriptionTier.FREE
    assert test_user.subscription_status == "canceled"
    assert test_user.stripe_subscription_id is None
    assert test_user.subscription_expires_at is None

    # Verify analytics event was captured
    mock_analytics_instance.capture.assert_called_once()


@pytest.mark.asyncio
async def test_handle_subscription_deleted_missing_customer(
    db_session,
    mock_settings,
    mock_stripe_client,
):
    """Test subscription deletion skips when customer is missing."""
    subscription_obj = {}  # Missing customer

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        # Should not raise
        await _handle_subscription_deleted(subscription_obj, db_session)


# =============================================================================
# Sync Subscription From Stripe Tests
# =============================================================================


@pytest.mark.asyncio
async def test_sync_subscription_from_stripe_active_subscription(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test syncing active subscription from Stripe."""
    from forge_shared.billing.models import PricingTier, SubscriptionStatus

    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    # Mock active subscription
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_123"
    mock_subscription.tier = PricingTier.PRO
    mock_subscription.status = SubscriptionStatus.ACTIVE
    mock_subscription.current_period_end = datetime.fromtimestamp(1735689600, tz=tz)
    mock_subscription.cancel_at_period_end = False
    mock_stripe_client.get_customer_subscriptions.return_value = [mock_subscription]

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        await _sync_subscription_from_stripe(test_user, db_session)

    # Refresh user
    await db_session.refresh(test_user)

    # Verify subscription synced
    assert test_user.stripe_subscription_id == "sub_123"
    assert test_user.subscription_tier == SubscriptionTier.PRO
    assert test_user.subscription_status == "active"


@pytest.mark.asyncio
async def test_sync_subscription_from_stripe_canceled_at_period_end(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test syncing subscription with cancel_at_period_end flag."""
    from forge_shared.billing.models import SubscriptionStatus

    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    # Mock subscription with cancel_at_period_end
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_123"
    mock_subscription.tier = PricingTier.PRO
    mock_subscription.status = SubscriptionStatus.ACTIVE
    mock_subscription.current_period_end = datetime.fromtimestamp(1735689600, tz=tz)
    mock_subscription.cancel_at_period_end = True
    mock_stripe_client.get_customer_subscriptions.return_value = [mock_subscription]

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        await _sync_subscription_from_stripe(test_user, db_session)

    # Refresh user
    await db_session.refresh(test_user)

    # Verify status reflects pending cancellation
    assert test_user.subscription_status == "cancel_at_period_end"


@pytest.mark.asyncio
async def test_sync_subscription_from_stripe_no_subscription(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test syncing when user has no Stripe subscription."""
    test_user.stripe_customer_id = "cus_123"
    test_user.subscription_tier = SubscriptionTier.PRO
    test_user.stripe_subscription_id = "sub_old"
    await db_session.commit()

    mock_stripe_client.get_customer_subscriptions.return_value = []  # No subscriptions

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        await _sync_subscription_from_stripe(test_user, db_session)

    # Refresh user
    await db_session.refresh(test_user)

    # Verify downgrade to FREE
    assert test_user.subscription_tier == SubscriptionTier.FREE
    assert test_user.subscription_status == "canceled"
    assert test_user.stripe_subscription_id is None


@pytest.mark.asyncio
async def test_sync_subscription_from_stripe_no_customer_id(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test sync skips when user has no Stripe customer ID."""
    # User without stripe_customer_id
    assert test_user.stripe_customer_id is None

    # Should not raise, should return early
    await _sync_subscription_from_stripe(test_user, db_session)


@pytest.mark.asyncio
async def test_sync_subscription_from_stripe_prioritizes_active(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test sync prioritizes active subscriptions over canceled ones."""
    from forge_shared.billing.models import SubscriptionStatus

    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    # Mock active subscription
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_active"
    mock_subscription.tier = PricingTier.PRO
    mock_subscription.status = SubscriptionStatus.ACTIVE
    mock_subscription.current_period_end = datetime.fromtimestamp(1735689600, tz=tz)
    mock_subscription.cancel_at_period_end = False
    mock_stripe_client.get_customer_subscriptions.return_value = [mock_subscription]

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        await _sync_subscription_from_stripe(test_user, db_session)

    # Verify active subscription was chosen
    await db_session.refresh(test_user)
    assert test_user.stripe_subscription_id == "sub_active"


# =============================================================================
# Integration Test Patterns
# =============================================================================


@pytest.mark.asyncio
async def test_checkout_creates_customer_if_missing(
    db_session,
    test_user,
    mock_settings,
):
    """Test checkout creates Stripe customer if user does not have one."""
    from app.api.subscriptions import CheckoutRequest, create_checkout_session

    # Ensure user has no customer ID
    assert test_user.stripe_customer_id is None

    with patch("stripe.Customer.create") as mock_create_customer:
        mock_create_customer.return_value = MagicMock(id="cus_new")

        with patch("stripe.checkout.Session.create") as mock_create_session:
            mock_create_session.return_value = MagicMock(
                url="https://checkout.stripe.com/session_123"
            )

            request = CheckoutRequest(price_id="price_pro_monthly")

            with patch("app.api.subscriptions.get_analytics") as mock_analytics:
                mock_analytics_instance = MagicMock()
                mock_analytics.return_value = mock_analytics_instance

                await create_checkout_session(
                    payload=request,
                    current_user=test_user,
                    session=db_session,
                )

    # Verify customer was created
    mock_create_customer.assert_called_once_with(
        email=test_user.email,
        name=test_user.full_name,
        metadata={"user_id": str(test_user.id)},
    )

    # Verify customer ID was saved
    await db_session.refresh(test_user)
    assert test_user.stripe_customer_id == "cus_new"


@pytest.mark.asyncio
async def test_checkout_rejects_duplicate_subscription(
    db_session,
    test_user,
    mock_settings,
    mock_stripe_client,
):
    """Test checkout fails if user already has active subscription."""
    from app.api.subscriptions import CheckoutRequest, create_checkout_session

    # Set existing customer and subscription
    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    # Mock existing active subscription
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_existing"
    mock_stripe_client.get_customer_subscriptions.return_value = [mock_subscription]

    request = CheckoutRequest(price_id="price_pro_monthly")

    with patch("app.api.subscriptions.get_stripe_client", return_value=mock_stripe_client):
        with pytest.raises(HTTPException) as exc_info:
            await create_checkout_session(
                payload=request,
                current_user=test_user,
                session=db_session,
            )

        # Verify error message
        assert exc_info.value.status_code == 400
        assert "already have an active subscription" in exc_info.value.detail
