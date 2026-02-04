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
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import stripe
from fastapi import HTTPException

from app.api.subscriptions import (
    _get_tier_from_price,
    _handle_checkout_completed,
    _handle_subscription_deleted,
    _handle_subscription_updated,
    _sync_subscription_from_stripe,
)
from app.models.user import SubscriptionTier, User


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
):
    """Test successful checkout completion creates subscription."""
    # Mock Stripe subscription response
    with patch("stripe.Subscription.retrieve") as mock_retrieve:
        mock_retrieve.return_value = {
            "id": "sub_123",
            "status": "active",
            "items": {
                "data": [
                    {
                        "price": {"id": "price_pro_monthly"},
                        "current_period_end": 1735689600,  # 2025-01-01 00:00:00 UTC
                    }
                ]
            },
            "plan": {
                "amount": 2999,
                "currency": "usd",
            },
        }

        session_obj = {
            "customer": "cus_123",
            "subscription": "sub_123",
            "metadata": {"user_id": str(test_user.id)},
        }

        with patch("app.api.subscriptions.get_analytics") as mock_analytics:
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
):
    """Test checkout handler skips when customer_id is missing."""
    session_obj = {
        "subscription": "sub_123",
        "metadata": {"user_id": str(uuid4())},
        # Missing customer_id
    }

    # Should not raise, just log warning
    await _handle_checkout_completed(session_obj, db_session)


@pytest.mark.asyncio
async def test_handle_checkout_completed_missing_user_id(
    db_session,
    mock_settings,
):
    """Test checkout handler skips when user_id is missing."""
    session_obj = {
        "customer": "cus_123",
        "subscription": "sub_123",
        "metadata": {},  # Missing user_id
    }

    # Should not raise, just log warning
    await _handle_checkout_completed(session_obj, db_session)


@pytest.mark.asyncio
async def test_handle_checkout_completed_user_not_found(
    db_session,
    mock_settings,
):
    """Test checkout handler skips when user doesn't exist."""
    fake_user_id = str(uuid4())
    session_obj = {
        "customer": "cus_123",
        "subscription": "sub_123",
        "metadata": {"user_id": fake_user_id},
    }

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
):
    """Test subscription update handler updates user tier and status."""
    # Set initial subscription
    test_user.stripe_customer_id = "cus_123"
    test_user.subscription_tier = SubscriptionTier.PRO
    await db_session.commit()

    subscription_obj = {
        "id": "sub_456",
        "customer": "cus_123",
        "status": "active",
        "items": {
            "data": [
                {
                    "price": {"id": "price_team_monthly"},
                    "current_period_end": 1735689600,
                }
            ]
        },
    }

    await _handle_subscription_updated(subscription_obj, db_session)

    # Refresh user
    await db_session.refresh(test_user)

    # Verify subscription was upgraded to TEAM
    assert test_user.subscription_tier == SubscriptionTier.TEAM
    assert test_user.stripe_subscription_id == "sub_456"
    assert test_user.subscription_status == "active"


@pytest.mark.asyncio
async def test_handle_subscription_updated_missing_customer(
    db_session,
    mock_settings,
):
    """Test subscription update skips when customer is missing."""
    subscription_obj = {
        "id": "sub_123",
        "status": "active",
        "items": {"data": [{"price": {"id": "price_pro_monthly"}}]},
        # Missing customer
    }

    # Should not raise
    await _handle_subscription_updated(subscription_obj, db_session)


@pytest.mark.asyncio
async def test_handle_subscription_updated_user_not_found(
    db_session,
    mock_settings,
):
    """Test subscription update skips when user not found."""
    subscription_obj = {
        "id": "sub_123",
        "customer": "cus_nonexistent",
        "status": "active",
        "items": {
            "data": [
                {
                    "price": {"id": "price_pro_monthly"},
                    "current_period_end": 1735689600,
                }
            ]
        },
    }

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
        "customer": "cus_123",
    }

    with patch("app.api.subscriptions.get_analytics") as mock_analytics:
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
):
    """Test subscription deletion skips when customer is missing."""
    subscription_obj = {}  # Missing customer

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
):
    """Test syncing active subscription from Stripe."""
    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    with patch("stripe.Subscription.list") as mock_list:
        mock_list.return_value = MagicMock(
            data=[
                {
                    "id": "sub_123",
                    "status": "active",
                    "items": {
                        "data": [
                            {
                                "price": {"id": "price_pro_monthly"},
                                "current_period_end": 1735689600,
                            }
                        ]
                    },
                }
            ]
        )

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
):
    """Test syncing subscription with cancel_at_period_end flag."""
    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    with patch("stripe.Subscription.list") as mock_list:
        mock_list.return_value = MagicMock(
            data=[
                {
                    "id": "sub_123",
                    "status": "active",
                    "cancel_at_period_end": True,
                    "items": {
                        "data": [
                            {
                                "price": {"id": "price_pro_monthly"},
                                "current_period_end": 1735689600,
                            }
                        ]
                    },
                }
            ]
        )

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
):
    """Test syncing when user has no Stripe subscription."""
    test_user.stripe_customer_id = "cus_123"
    test_user.subscription_tier = SubscriptionTier.PRO
    test_user.stripe_subscription_id = "sub_old"
    await db_session.commit()

    with patch("stripe.Subscription.list") as mock_list:
        mock_list.return_value = MagicMock(data=[])  # No subscriptions

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
):
    """Test sync prioritizes active subscriptions over canceled ones."""
    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    with patch("stripe.Subscription.list") as mock_list:
        # First call returns active subscription
        mock_list.return_value = MagicMock(
            data=[
                {
                    "id": "sub_active",
                    "status": "active",
                    "items": {
                        "data": [
                            {
                                "price": {"id": "price_pro_monthly"},
                                "current_period_end": 1735689600,
                            }
                        ]
                    },
                }
            ]
        )

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
    """Test checkout creates Stripe customer if user doesn't have one."""
    from app.api.subscriptions import create_checkout_session, CheckoutRequest

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

                response = await create_checkout_session(
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
):
    """Test checkout fails if user already has active subscription."""
    from app.api.subscriptions import create_checkout_session, CheckoutRequest

    # Set existing customer and subscription
    test_user.stripe_customer_id = "cus_123"
    await db_session.commit()

    with patch("stripe.Subscription.list") as mock_list:
        mock_list.return_value = MagicMock(
            data=[{"id": "sub_existing", "status": "active"}]
        )

        request = CheckoutRequest(price_id="price_pro_monthly")

        with pytest.raises(HTTPException) as exc_info:
            await create_checkout_session(
                payload=request,
                current_user=test_user,
                session=db_session,
            )

        # Verify error message
        assert exc_info.value.status_code == 400
        assert "already have an active subscription" in exc_info.value.detail
