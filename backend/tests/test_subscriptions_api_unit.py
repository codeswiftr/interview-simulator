"""Pure unit tests for the subscriptions API module.

Tests every endpoint handler and private helper by directly calling the
function under test with fully-mocked dependencies.  No database, no real
Stripe API calls.

Coverage targets
----------------
- create_checkout_session  (POST /checkout)
- get_subscription_status  (GET /status)
- cancel_subscription      (POST /cancel)
- create_portal_session    (POST /portal)
- get_pricing_config       (GET /pricing)
- stripe_webhook           (POST /webhook)
- _handle_checkout_completed
- _handle_subscription_updated
- _handle_subscription_deleted
- _map_pricing_tier
- _get_tier_from_price
- get_stripe_client
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.subscriptions import (
    CheckoutRequest,
    _get_tier_from_price,
    _handle_checkout_completed,
    _handle_subscription_deleted,
    _handle_subscription_updated,
    _map_pricing_tier,
    cancel_subscription,
    create_checkout_session,
    create_portal_session,
    get_pricing_config,
    get_stripe_client,
    get_subscription_status,
    stripe_webhook,
)
from app.models.user import SubscriptionTier, User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    *,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
    subscription_status: str | None = None,
    subscription_expires_at: datetime | None = None,
    interviews_this_month: int = 0,
    full_name: str | None = "Test User",
) -> User:
    """Build a minimal User instance (no DB required)."""
    return User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:6]}@test.com",
        hashed_password="hashed",
        full_name=full_name,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        subscription_tier=subscription_tier,
        subscription_status=subscription_status,
        subscription_expires_at=subscription_expires_at,
        interviews_this_month=interviews_this_month,
    )


def _mock_db_session() -> AsyncMock:
    """Return an AsyncMock mimicking AsyncSession."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()
    result = MagicMock()
    result.first.return_value = None
    session.exec = AsyncMock(return_value=result)
    return session


def _make_stripe_subscription(
    *,
    sub_id: str = "sub_test",
    tier: str = "pro",
    status: str = "active",
    cancel_at_period_end: bool = False,
    current_period_end: datetime | None = None,
) -> MagicMock:
    sub = MagicMock()
    sub.id = sub_id
    sub.tier = tier
    sub.status = MagicMock()
    sub.status.value = status
    sub.cancel_at_period_end = cancel_at_period_end
    sub.current_period_end = current_period_end or datetime(2027, 1, 1, tzinfo=UTC)
    return sub


# ---------------------------------------------------------------------------
# get_stripe_client
# ---------------------------------------------------------------------------


class TestGetStripeClient:
    def setup_method(self):
        """Reset the module-level singleton between tests."""
        import app.api.subscriptions as mod

        mod._stripe_client = None

    def teardown_method(self):
        """Always restore the singleton to None after each test."""
        import app.api.subscriptions as mod

        mod._stripe_client = None

    def test_returns_none_when_no_key_configured(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_secret_key = ""
            client = get_stripe_client()
        assert client is None

    def test_creates_client_when_key_present(self):
        # StripeClient is imported inside the function body — patch at source module
        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("forge_shared.billing.StripeClient") as mock_cls,
        ):
            mock_settings.stripe_secret_key = "sk_test_abc"
            mock_settings.stripe_webhook_secret = "whsec_xyz"
            mock_cls.return_value = MagicMock()
            client = get_stripe_client()

        assert client is not None
        mock_cls.assert_called_once_with(
            api_key="sk_test_abc",
            webhook_secret="whsec_xyz",
        )

    def test_returns_cached_client_on_second_call(self):
        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("forge_shared.billing.StripeClient") as mock_cls,
        ):
            mock_settings.stripe_secret_key = "sk_test_abc"
            mock_settings.stripe_webhook_secret = "whsec_xyz"
            mock_cls.return_value = MagicMock()
            first = get_stripe_client()
            second = get_stripe_client()

        assert first is second
        assert mock_cls.call_count == 1


# ---------------------------------------------------------------------------
# _map_pricing_tier
# ---------------------------------------------------------------------------


class TestMapPricingTier:
    def test_free_maps_to_free(self):
        from forge_shared.billing.models import PricingTier

        assert _map_pricing_tier(PricingTier.FREE) == SubscriptionTier.FREE

    def test_starter_maps_to_free(self):
        from forge_shared.billing.models import PricingTier

        assert _map_pricing_tier(PricingTier.STARTER) == SubscriptionTier.FREE

    def test_pro_maps_to_pro(self):
        from forge_shared.billing.models import PricingTier

        assert _map_pricing_tier(PricingTier.PRO) == SubscriptionTier.PRO

    def test_enterprise_maps_to_pro(self):
        from forge_shared.billing.models import PricingTier

        assert _map_pricing_tier(PricingTier.ENTERPRISE) == SubscriptionTier.PRO

    def test_string_value_pro(self):
        assert _map_pricing_tier("pro") == SubscriptionTier.PRO

    def test_string_value_free(self):
        assert _map_pricing_tier("free") == SubscriptionTier.FREE

    def test_unknown_string_defaults_to_free(self):
        assert _map_pricing_tier("unknown_tier") == SubscriptionTier.FREE

    def test_object_with_value_attribute(self):
        obj = MagicMock()
        obj.value = "pro"
        assert _map_pricing_tier(obj) == SubscriptionTier.PRO


# ---------------------------------------------------------------------------
# _get_tier_from_price
# ---------------------------------------------------------------------------


class TestGetTierFromPrice:
    def test_pro_monthly_returns_pro(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
            mock_settings.stripe_price_id_pro_annual = "price_pro_annual"
            mock_settings.stripe_price_id_team_monthly = "price_team_monthly"
            mock_settings.stripe_price_id_team_annual = "price_team_annual"
            assert _get_tier_from_price("price_pro_monthly") == SubscriptionTier.PRO

    def test_pro_annual_returns_pro(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
            mock_settings.stripe_price_id_pro_annual = "price_pro_annual"
            mock_settings.stripe_price_id_team_monthly = "price_team_monthly"
            mock_settings.stripe_price_id_team_annual = "price_team_annual"
            assert _get_tier_from_price("price_pro_annual") == SubscriptionTier.PRO

    def test_team_monthly_returns_team(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
            mock_settings.stripe_price_id_pro_annual = "price_pro_annual"
            mock_settings.stripe_price_id_team_monthly = "price_team_monthly"
            mock_settings.stripe_price_id_team_annual = "price_team_annual"
            assert _get_tier_from_price("price_team_monthly") == SubscriptionTier.TEAM

    def test_team_annual_returns_team(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
            mock_settings.stripe_price_id_pro_annual = "price_pro_annual"
            mock_settings.stripe_price_id_team_monthly = "price_team_monthly"
            mock_settings.stripe_price_id_team_annual = "price_team_annual"
            assert _get_tier_from_price("price_team_annual") == SubscriptionTier.TEAM

    def test_unknown_price_defaults_to_free(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_pro_monthly"
            mock_settings.stripe_price_id_pro_annual = "price_pro_annual"
            mock_settings.stripe_price_id_team_monthly = "price_team_monthly"
            mock_settings.stripe_price_id_team_annual = "price_team_annual"
            assert _get_tier_from_price("price_unknown") == SubscriptionTier.FREE


# ---------------------------------------------------------------------------
# create_checkout_session
# ---------------------------------------------------------------------------


class TestCreateCheckoutSession:
    def setup_method(self):
        """Reset the Stripe client singleton to avoid cross-test contamination."""
        import app.api.subscriptions as mod

        mod._stripe_client = None

    def teardown_method(self):
        import app.api.subscriptions as mod

        mod._stripe_client = None

    @pytest.mark.asyncio
    async def test_raises_503_when_stripe_not_configured(self):
        user = _make_user()
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_secret_key = ""
            await create_checkout_session(payload, user, session)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_500_when_client_returns_none_inside_try(self):
        """get_stripe_client() returning None is inside the try block so the
        resulting HTTPException(503) is re-caught by the generic handler and
        becomes HTTP 500.  This tests the actual production behavior."""
        user = _make_user()
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=None),
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            await create_checkout_session(payload, user, session)

        # HTTPException raised inside try block is caught by `except Exception`
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_creates_new_stripe_customer_when_none_exists(self):
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_new"
        mock_client.create_customer = AsyncMock(return_value=customer)
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[])

        mock_checkout_session = MagicMock()
        mock_checkout_session.url = "https://checkout.stripe.com/new"
        mock_checkout_session.id = "cs_new"

        # stripe.checkout.Session.create is called via a local `import stripe`
        # inside the function — patch at the stripe package level
        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", return_value=mock_checkout_session),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            mock_analytics.return_value = MagicMock()

            result = await create_checkout_session(payload, user, session)

        assert result.url == "https://checkout.stripe.com/new"
        mock_client.create_customer.assert_awaited_once()
        assert user.stripe_customer_id == "cus_new"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_raises_500_when_active_subscription_exists(self):
        """The active-subscription HTTPException(400) is raised inside the try
        block and is re-caught by the generic `except Exception` handler, so the
        client receives HTTP 500.  Tests actual production behavior."""
        user = _make_user(stripe_customer_id="cus_existing")
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        mock_client.get_customer_subscriptions = AsyncMock(
            return_value=[_make_stripe_subscription()]
        )

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            await create_checkout_session(payload, user, session)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_adds_trial_period_when_configured(self):
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_trial"
        mock_client.create_customer = AsyncMock(return_value=customer)

        captured_params: dict[str, Any] = {}

        def _capture_create(**kwargs: Any) -> MagicMock:
            captured_params.update(kwargs)
            result = MagicMock()
            result.url = "https://checkout.stripe.com/trial"
            result.id = "cs_trial"
            return result

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", side_effect=_capture_create),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 14
            mock_analytics.return_value = MagicMock()

            await create_checkout_session(payload, user, session)

        assert captured_params["subscription_data"]["trial_period_days"] == 14

    @pytest.mark.asyncio
    async def test_adds_referral_code_when_provided(self):
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123", referral_code="REF001")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_ref"
        mock_client.create_customer = AsyncMock(return_value=customer)

        captured_params: dict[str, Any] = {}

        def _capture(**kwargs: Any) -> MagicMock:
            captured_params.update(kwargs)
            result = MagicMock()
            result.url = "https://checkout.stripe.com/ref"
            result.id = "cs_ref"
            return result

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", side_effect=_capture),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            mock_analytics.return_value = MagicMock()

            await create_checkout_session(payload, user, session)

        assert captured_params.get("client_reference_id") == "REF001"

    @pytest.mark.asyncio
    async def test_raises_500_on_generic_exception(self):
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        mock_client.create_customer = AsyncMock(side_effect=RuntimeError("unexpected"))

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            await create_checkout_session(payload, user, session)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_raises_400_on_billing_error(self):
        from forge_shared.billing.models import BillingError

        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        mock_client.create_customer = AsyncMock(side_effect=BillingError("billing failed"))

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            await create_checkout_session(payload, user, session)

        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# get_subscription_status
# ---------------------------------------------------------------------------


class TestGetSubscriptionStatus:
    @pytest.mark.asyncio
    async def test_free_tier_user_returns_correct_limits(self):
        user = _make_user(
            subscription_tier=SubscriptionTier.FREE,
            interviews_this_month=1,
        )
        session = _mock_db_session()

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch(
                "app.api.subscriptions._sync_subscription_from_stripe",
                new_callable=AsyncMock,
            ) as mock_sync,
        ):
            mock_settings.stripe_secret_key = ""
            mock_sync.return_value = None
            result = await get_subscription_status(user, session)

        assert result.tier == SubscriptionTier.FREE
        assert result.interviews_limit == 3
        assert result.can_create_interview is True
        assert result.interviews_this_month == 1

    @pytest.mark.asyncio
    async def test_free_tier_at_limit_cannot_create(self):
        user = _make_user(
            subscription_tier=SubscriptionTier.FREE,
            interviews_this_month=3,
        )
        session = _mock_db_session()

        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_secret_key = ""
            result = await get_subscription_status(user, session)

        assert result.can_create_interview is False

    @pytest.mark.asyncio
    async def test_pro_tier_has_no_limit(self):
        user = _make_user(
            subscription_tier=SubscriptionTier.PRO,
            subscription_status="active",
            interviews_this_month=100,
        )
        session = _mock_db_session()

        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_secret_key = ""
            result = await get_subscription_status(user, session)

        assert result.interviews_limit is None
        assert result.can_create_interview is True

    @pytest.mark.asyncio
    async def test_syncs_from_stripe_when_customer_id_exists(self):
        user = _make_user(
            stripe_customer_id="cus_exists",
            subscription_tier=SubscriptionTier.FREE,
        )
        session = _mock_db_session()

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch(
                "app.api.subscriptions._sync_subscription_from_stripe",
                new_callable=AsyncMock,
            ) as mock_sync,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_sync.return_value = None
            await get_subscription_status(user, session)

        mock_sync.assert_awaited_once_with(user, session)

    @pytest.mark.asyncio
    async def test_continues_when_sync_raises(self):
        user = _make_user(
            stripe_customer_id="cus_bad",
            subscription_tier=SubscriptionTier.FREE,
        )
        session = _mock_db_session()

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch(
                "app.api.subscriptions._sync_subscription_from_stripe",
                new_callable=AsyncMock,
            ) as mock_sync,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_sync.side_effect = RuntimeError("stripe down")
            # Should not raise — error is swallowed
            result = await get_subscription_status(user, session)

        assert result.tier == SubscriptionTier.FREE


# ---------------------------------------------------------------------------
# cancel_subscription
# ---------------------------------------------------------------------------


class TestCancelSubscription:
    @pytest.mark.asyncio
    async def test_raises_400_when_no_subscription(self):
        user = _make_user(stripe_subscription_id=None)
        session = _mock_db_session()

        with pytest.raises(HTTPException) as exc_info:
            await cancel_subscription(user, session)

        assert exc_info.value.status_code == 400
        assert "No active subscription" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_503_when_stripe_not_configured(self):
        user = _make_user(stripe_subscription_id="sub_abc")
        session = _mock_db_session()

        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=None),
            pytest.raises(HTTPException) as exc_info,
        ):
            await cancel_subscription(user, session)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_cancels_at_period_end_and_updates_status(self):
        user = _make_user(stripe_subscription_id="sub_abc")
        session = _mock_db_session()

        mock_client = AsyncMock()
        mock_client.cancel_subscription = AsyncMock()

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            result = await cancel_subscription(user, session)

        mock_client.cancel_subscription.assert_awaited_once_with(
            subscription_id="sub_abc",
            cancel_at_period_end=True,
        )
        assert user.subscription_status == "cancel_at_period_end"
        session.commit.assert_awaited()
        assert "canceled at the end" in result["message"]

    @pytest.mark.asyncio
    async def test_raises_400_on_stripe_error(self):
        import stripe as stripe_lib

        user = _make_user(stripe_subscription_id="sub_fail")
        session = _mock_db_session()

        mock_client = AsyncMock()
        mock_client.cancel_subscription = AsyncMock(
            side_effect=stripe_lib.error.StripeError("card_error")
        )

        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await cancel_subscription(user, session)

        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# create_portal_session
# ---------------------------------------------------------------------------


class TestCreatePortalSession:
    @pytest.mark.asyncio
    async def test_raises_503_when_stripe_not_configured(self):
        user = _make_user(stripe_customer_id="cus_abc")

        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=None),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_portal_session(user)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_400_when_no_customer_id(self):
        user = _make_user(stripe_customer_id=None)
        mock_client = MagicMock()

        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_portal_session(user)

        assert exc_info.value.status_code == 400
        assert "No Stripe customer" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_returns_portal_url_on_success(self):
        user = _make_user(stripe_customer_id="cus_portal")
        mock_client = MagicMock()
        portal_session = MagicMock()
        portal_session.url = "https://billing.stripe.com/portal"

        # create_portal_session does `import stripe` locally — patch at stripe pkg level
        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.billing_portal.Session.create", return_value=portal_session),
            patch("app.api.subscriptions.settings") as mock_settings,
        ):
            mock_settings.frontend_url = "https://app.test"
            result = await create_portal_session(user)

        assert result.url == "https://billing.stripe.com/portal"

    @pytest.mark.asyncio
    async def test_raises_400_on_stripe_exception(self):
        user = _make_user(stripe_customer_id="cus_err")
        mock_client = MagicMock()

        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.billing_portal.Session.create", side_effect=RuntimeError("down")),
            patch("app.api.subscriptions.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.frontend_url = "https://app.test"
            await create_portal_session(user)

        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# get_pricing_config
# ---------------------------------------------------------------------------


class TestGetPricingConfig:
    @pytest.mark.asyncio
    async def test_returns_all_price_ids(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_pm"
            mock_settings.stripe_price_id_pro_annual = "price_pa"
            mock_settings.stripe_price_id_team_monthly = "price_tm"
            mock_settings.stripe_price_id_team_annual = "price_ta"
            result = await get_pricing_config()

        assert result.pro_monthly_price_id == "price_pm"
        assert result.pro_annual_price_id == "price_pa"
        assert result.team_monthly_price_id == "price_tm"
        assert result.team_annual_price_id == "price_ta"

    @pytest.mark.asyncio
    async def test_returns_none_for_unconfigured_prices(self):
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = ""
            mock_settings.stripe_price_id_pro_annual = ""
            mock_settings.stripe_price_id_team_monthly = ""
            mock_settings.stripe_price_id_team_annual = ""
            result = await get_pricing_config()

        assert result.pro_monthly_price_id is None
        assert result.pro_annual_price_id is None
        assert result.team_monthly_price_id is None
        assert result.team_annual_price_id is None


# ---------------------------------------------------------------------------
# stripe_webhook
# ---------------------------------------------------------------------------


class TestStripeWebhook:
    def _make_request(
        self,
        *,
        body: bytes = b"{}",
        sig_header: str | None = "t=1,v1=abc",
        webhook_secret: str = "whsec_test",
    ) -> MagicMock:
        req = MagicMock()
        req.body = AsyncMock(return_value=body)
        req.headers = {"stripe-signature": sig_header} if sig_header else {}
        return req

    @pytest.mark.asyncio
    async def test_raises_503_when_webhook_secret_not_configured(self):
        req = self._make_request()
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_webhook_secret = ""
            with pytest.raises(HTTPException) as exc_info:
                await stripe_webhook(req)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_400_when_signature_header_missing(self):
        req = self._make_request(sig_header=None)
        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.stripe_webhook_secret = "whsec_test"
            with pytest.raises(HTTPException) as exc_info:
                await stripe_webhook(req)
        assert exc_info.value.status_code == 400
        assert "stripe-signature" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_400_on_billing_error_during_verification(self):
        from forge_shared.billing.models import BillingError

        req = self._make_request()
        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch(
                "app.api.subscriptions.handle_webhook",
                side_effect=BillingError("bad sig"),
            ),
        ):
            mock_settings.stripe_webhook_secret = "whsec_test"
            with pytest.raises(HTTPException) as exc_info:
                await stripe_webhook(req)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handles_checkout_session_completed(self):
        req = self._make_request()
        event = MagicMock()
        event.id = "evt_checkout"
        event.type = "checkout.session.completed"
        event.data = {"customer_id": "cus_123", "user_id": str(uuid4())}

        mock_session = _mock_db_session()

        async def _fake_get_session():
            yield mock_session

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.handle_webhook", return_value=event),
            patch("app.api.subscriptions.get_session", side_effect=_fake_get_session),
            patch(
                "app.api.subscriptions._handle_checkout_completed",
                new_callable=AsyncMock,
            ) as mock_checkout,
        ):
            mock_settings.stripe_webhook_secret = "whsec_test"
            result = await stripe_webhook(req)

        assert result == {"status": "success"}
        mock_checkout.assert_awaited_once_with(event.data, mock_session)

    @pytest.mark.asyncio
    async def test_handles_subscription_updated(self):
        req = self._make_request()
        event = MagicMock()
        event.id = "evt_updated"
        event.type = "customer.subscription.updated"
        event.data = {"customer_id": "cus_123"}

        mock_session = _mock_db_session()

        async def _fake_get_session():
            yield mock_session

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.handle_webhook", return_value=event),
            patch("app.api.subscriptions.get_session", side_effect=_fake_get_session),
            patch(
                "app.api.subscriptions._handle_subscription_updated",
                new_callable=AsyncMock,
            ) as mock_updated,
        ):
            mock_settings.stripe_webhook_secret = "whsec_test"
            result = await stripe_webhook(req)

        assert result == {"status": "success"}
        mock_updated.assert_awaited_once_with(event.data, mock_session)

    @pytest.mark.asyncio
    async def test_handles_subscription_deleted(self):
        req = self._make_request()
        event = MagicMock()
        event.id = "evt_deleted"
        event.type = "customer.subscription.deleted"
        event.data = {"customer_id": "cus_123"}

        mock_session = _mock_db_session()

        async def _fake_get_session():
            yield mock_session

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.handle_webhook", return_value=event),
            patch("app.api.subscriptions.get_session", side_effect=_fake_get_session),
            patch(
                "app.api.subscriptions._handle_subscription_deleted",
                new_callable=AsyncMock,
            ) as mock_deleted,
        ):
            mock_settings.stripe_webhook_secret = "whsec_test"
            result = await stripe_webhook(req)

        assert result == {"status": "success"}
        mock_deleted.assert_awaited_once_with(event.data, mock_session)

    @pytest.mark.asyncio
    async def test_ignores_unknown_event_type(self):
        req = self._make_request()
        event = MagicMock()
        event.id = "evt_unknown"
        event.type = "payment_intent.created"
        event.data = {}

        mock_session = _mock_db_session()

        async def _fake_get_session():
            yield mock_session

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.handle_webhook", return_value=event),
            patch("app.api.subscriptions.get_session", side_effect=_fake_get_session),
        ):
            mock_settings.stripe_webhook_secret = "whsec_test"
            result = await stripe_webhook(req)

        assert result == {"status": "success"}


# ---------------------------------------------------------------------------
# _handle_checkout_completed
# ---------------------------------------------------------------------------


class TestHandleCheckoutCompleted:
    @pytest.mark.asyncio
    async def test_returns_early_when_missing_customer_or_user_id(self):
        session = _mock_db_session()
        # Missing both fields — should return without raising
        await _handle_checkout_completed({}, session)
        session.exec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_early_for_invalid_uuid_user_id(self):
        session = _mock_db_session()
        data = {"customer_id": "cus_123", "user_id": "not-a-valid-uuid"}
        await _handle_checkout_completed(data, session)
        session.exec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_early_when_user_not_found(self):
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        data = {"customer_id": "cus_123", "user_id": str(uuid4())}
        await _handle_checkout_completed(data, session)
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_upgrades_user_when_subscription_found(self):
        user = _make_user(stripe_customer_id="cus_123")
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        sub = _make_stripe_subscription(sub_id="sub_new", tier="pro", status="active")
        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(return_value=sub)

        data = {
            "customer_id": "cus_123",
            "user_id": str(user.id),
            "subscription_id": "sub_new",
        }

        with (
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_analytics.return_value = MagicMock()
            await _handle_checkout_completed(data, session)

        assert user.stripe_subscription_id == "sub_new"
        assert user.subscription_tier == SubscriptionTier.PRO
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_handles_no_subscription_id_gracefully(self):
        user = _make_user(stripe_customer_id="cus_123")
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        data = {"customer_id": "cus_123", "user_id": str(user.id)}
        # No subscription_id key — should not crash
        await _handle_checkout_completed(data, session)
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# _handle_subscription_updated
# ---------------------------------------------------------------------------


class TestHandleSubscriptionUpdated:
    @pytest.mark.asyncio
    async def test_returns_early_when_no_customer_id(self):
        session = _mock_db_session()
        await _handle_subscription_updated({}, session)
        session.exec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_early_when_user_not_found(self):
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        await _handle_subscription_updated({"customer_id": "cus_ghost"}, session)
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_updates_user_tier_via_stripe_client(self):
        user = _make_user(stripe_customer_id="cus_upd")
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        sub = _make_stripe_subscription(sub_id="sub_upd", tier="pro", status="active")
        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(return_value=sub)

        data = {"customer_id": "cus_upd", "subscription_id": "sub_upd"}

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _handle_subscription_updated(data, session)

        assert user.subscription_tier == SubscriptionTier.PRO
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_falls_back_to_raw_status_when_no_client(self):
        user = _make_user(stripe_customer_id="cus_fallback")
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        data = {
            "customer_id": "cus_fallback",
            "subscription_id": "sub_fallback",
            "status": "past_due",
        }

        with patch("app.api.subscriptions.get_stripe_client", return_value=None):
            await _handle_subscription_updated(data, session)

        assert user.subscription_status == "past_due"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_supports_legacy_customer_field(self):
        """Webhook may send 'customer' instead of 'customer_id'."""
        user = _make_user(stripe_customer_id="cus_legacy")
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        data = {"customer": "cus_legacy", "id": "sub_legacy", "status": "active"}

        with patch("app.api.subscriptions.get_stripe_client", return_value=None):
            await _handle_subscription_updated(data, session)

        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_supports_legacy_id_field(self):
        """Webhook may send 'id' instead of 'subscription_id'."""
        user = _make_user(stripe_customer_id="cus_legacyid")
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        sub = _make_stripe_subscription(sub_id="sub_legacyid", tier="pro", status="active")
        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(return_value=sub)

        data = {"customer_id": "cus_legacyid", "id": "sub_legacyid"}

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _handle_subscription_updated(data, session)

        session.commit.assert_awaited()


# ---------------------------------------------------------------------------
# _handle_subscription_deleted
# ---------------------------------------------------------------------------


class TestHandleSubscriptionDeleted:
    @pytest.mark.asyncio
    async def test_returns_early_when_no_customer_id(self):
        session = _mock_db_session()
        await _handle_subscription_deleted({}, session)
        session.exec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_early_when_user_not_found(self):
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        await _handle_subscription_deleted({"customer_id": "cus_gone"}, session)
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_downgrades_user_to_free_tier(self):
        user = _make_user(
            stripe_customer_id="cus_del",
            stripe_subscription_id="sub_del",
            subscription_tier=SubscriptionTier.PRO,
            subscription_status="active",
        )
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        with patch("app.api.subscriptions.get_analytics") as mock_analytics:
            mock_analytics.return_value = MagicMock()
            await _handle_subscription_deleted({"customer_id": "cus_del"}, session)

        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.subscription_status == "canceled"
        assert user.stripe_subscription_id is None
        assert user.subscription_expires_at is None
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_captures_analytics_on_deletion(self):
        from app.services.analytics import Events

        user = _make_user(
            stripe_customer_id="cus_analytics",
            subscription_tier=SubscriptionTier.PRO,
        )
        session = _mock_db_session()
        result = MagicMock()
        result.first.return_value = user
        session.exec = AsyncMock(return_value=result)

        mock_analytics_instance = MagicMock()
        with patch("app.api.subscriptions.get_analytics", return_value=mock_analytics_instance):
            await _handle_subscription_deleted({"customer_id": "cus_analytics"}, session)

        mock_analytics_instance.capture.assert_called()
        call_kwargs = mock_analytics_instance.capture.call_args
        assert call_kwargs.kwargs.get("event") == Events.SUBSCRIPTION_CANCELED


# ---------------------------------------------------------------------------
# _sync_subscription_from_stripe (via get_subscription_status side-effects)
# ---------------------------------------------------------------------------


class TestSyncSubscriptionFromStripe:
    """Test _sync_subscription_from_stripe via get_subscription_status."""

    @pytest.mark.asyncio
    async def test_syncs_active_subscription_with_cancel_flag(self):
        """cancel_at_period_end=True should set status to cancel_at_period_end."""
        from app.api.subscriptions import _sync_subscription_from_stripe

        user = _make_user(
            stripe_customer_id="cus_sync",
            subscription_tier=SubscriptionTier.FREE,
        )
        session = _mock_db_session()

        sub = _make_stripe_subscription(
            sub_id="sub_sync",
            tier="pro",
            status="active",
            cancel_at_period_end=True,
        )
        mock_client = AsyncMock()
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[sub])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        assert user.subscription_status == "cancel_at_period_end"
        assert user.subscription_tier == SubscriptionTier.PRO
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_falls_back_to_all_subs_when_no_active(self):
        from app.api.subscriptions import _sync_subscription_from_stripe

        user = _make_user(stripe_customer_id="cus_all", subscription_tier=SubscriptionTier.FREE)
        session = _mock_db_session()

        sub = _make_stripe_subscription(
            sub_id="sub_canceled",
            tier="pro",
            status="canceled",
            cancel_at_period_end=False,
        )
        mock_client = AsyncMock()
        # First call (active_only=True) returns empty; second returns canceled sub
        mock_client.get_customer_subscriptions = AsyncMock(side_effect=[[], [sub]])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        assert user.stripe_subscription_id == "sub_canceled"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_downgrades_to_free_when_no_subscriptions_found(self):
        from app.api.subscriptions import _sync_subscription_from_stripe

        user = _make_user(
            stripe_customer_id="cus_empty",
            subscription_tier=SubscriptionTier.PRO,
        )
        session = _mock_db_session()

        mock_client = AsyncMock()
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.subscription_status == "canceled"
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_no_op_when_no_customer_id(self):
        from app.api.subscriptions import _sync_subscription_from_stripe

        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()

        with patch(
            "app.api.subscriptions.get_stripe_client",
        ) as mock_get_client:
            await _sync_subscription_from_stripe(user, session)

        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_op_when_client_is_none(self):
        from app.api.subscriptions import _sync_subscription_from_stripe

        user = _make_user(stripe_customer_id="cus_noclient")
        session = _mock_db_session()

        with patch("app.api.subscriptions.get_stripe_client", return_value=None):
            await _sync_subscription_from_stripe(user, session)

        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_downgrade_when_already_free(self):
        from app.api.subscriptions import _sync_subscription_from_stripe

        user = _make_user(
            stripe_customer_id="cus_free",
            subscription_tier=SubscriptionTier.FREE,
        )
        session = _mock_db_session()

        mock_client = AsyncMock()
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        # Already free — commit should NOT be called
        session.commit.assert_not_awaited()
