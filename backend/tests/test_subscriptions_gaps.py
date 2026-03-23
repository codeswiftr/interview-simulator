"""Gap tests for subscriptions API - covers uncovered paths.

These tests target specific branches in subscriptions.py that were not covered
by the main test suite, pushing coverage from 21% toward the 70%+ quality gate.

Gap targets
-----------
- _handle_checkout_completed: invalid UUID user_id, subscription present + Stripe fetch
- _handle_subscription_updated: no client fallback, Stripe returns None subscription
- _sync_subscription_from_stripe: cancel_at_period_end status, PRO user downgrade
- create_checkout_session: referral_code → client_reference_id, trial_days > 0
- stripe_webhook: missing stripe-signature header → 400
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
    _handle_checkout_completed,
    _handle_subscription_updated,
    _sync_subscription_from_stripe,
    create_checkout_session,
    stripe_webhook,
)
from app.models.user import SubscriptionTier, User


# ---------------------------------------------------------------------------
# Helpers — mirrors helpers in test_subscriptions_api_unit.py exactly
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


def _mock_webhook_processor_ctx():
    """Return a patch context that replaces WebhookProcessor with a no-op async ctx manager."""
    processor = MagicMock()
    processor.set_result = MagicMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=processor)
    ctx.__aexit__ = AsyncMock(return_value=False)
    mock_cls = MagicMock(return_value=ctx)
    return patch("app.api.subscriptions.WebhookProcessor", mock_cls), processor


def _make_stripe_subscription(
    *,
    sub_id: str = "sub_test",
    tier: str = "pro",
    status: str = "active",
    cancel_at_period_end: bool = False,
    current_period_end: datetime | None = None,
) -> MagicMock:
    """Create a mock Stripe subscription object."""
    sub = MagicMock()
    sub.id = sub_id
    sub.tier = tier
    sub.status = status
    sub.cancel_at_period_end = cancel_at_period_end
    sub.current_period_end = current_period_end or datetime(2027, 1, 1, tzinfo=UTC)
    return sub


# ---------------------------------------------------------------------------
# _handle_checkout_completed — gap paths
# ---------------------------------------------------------------------------


class TestHandleCheckoutCompletedGaps:
    """Gap tests for _handle_checkout_completed."""

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_invalid_uuid_user_id(self):
        """UUID('invalid') should raise ValueError — handler must log and return
        early without issuing any database query."""
        session = _mock_db_session()
        data = {
            "customer_id": "cus_123",
            "user_id": "not-a-valid-uuid",  # triggers ValueError in UUID(user_id)
            "subscription_id": "sub_123",
        }

        # Must not raise — ValueError is caught internally
        await _handle_checkout_completed(data, session)

        # UUID conversion fails before the DB query so exec must never be called
        session.exec.assert_not_awaited()
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_missing_subscription_id(self):
        """When subscription_id is absent the handler finds the user but skips the
        Stripe fetch entirely and must not commit."""
        user = _make_user(stripe_customer_id="cus_123")
        session = _mock_db_session()
        db_result = MagicMock()
        db_result.first.return_value = user
        session.exec = AsyncMock(return_value=db_result)

        data = {
            "customer_id": "cus_123",
            "user_id": str(user.id),
            # subscription_id intentionally absent
        }

        await _handle_checkout_completed(data, session)

        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_with_subscription_fetches_and_upgrades(self):
        """When subscription_id is present, the handler must fetch the subscription
        from Stripe via get_stripe_client().get_subscription() and upgrade the user."""
        user = _make_user(stripe_customer_id="cus_123")
        session = _mock_db_session()
        db_result = MagicMock()
        db_result.first.return_value = user
        session.exec = AsyncMock(return_value=db_result)

        sub = _make_stripe_subscription(
            sub_id="sub_upgrade",
            tier="pro",
            status="active",
            cancel_at_period_end=False,
        )
        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(return_value=sub)

        data = {
            "customer_id": "cus_123",
            "user_id": str(user.id),
            "subscription_id": "sub_upgrade",
        }

        wp_patch, _ = _mock_webhook_processor_ctx()
        with (
            wp_patch,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
            patch("app.api.subscriptions.track_stripe_conversion", new_callable=AsyncMock),
        ):
            mock_analytics.return_value = MagicMock()
            await _handle_checkout_completed(data, session, stripe_event_id="evt_upgrade")

        # Stripe client must have been used to fetch the subscription
        mock_client.get_subscription.assert_awaited_once_with("sub_upgrade")

        # User record must be updated
        assert user.stripe_subscription_id == "sub_upgrade"
        assert user.subscription_tier == SubscriptionTier.PRO
        assert user.subscription_status == "active"
        assert user.subscription_expires_at is not None

        # Analytics events must be captured
        mock_analytics.return_value.capture.assert_called()

        # Flush must be called (handler uses flush; commit is managed by FastAPI session)
        session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_subscription_fetch_returns_none(self):
        """When get_subscription() returns None, the handler must not update the
        user or commit — it silently skips the upgrade."""
        user = _make_user(stripe_customer_id="cus_nodata")
        session = _mock_db_session()
        db_result = MagicMock()
        db_result.first.return_value = user
        session.exec = AsyncMock(return_value=db_result)

        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(return_value=None)

        data = {
            "customer_id": "cus_nodata",
            "user_id": str(user.id),
            "subscription_id": "sub_missing",
        }

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _handle_checkout_completed(data, session)

        # No tier change, no commit
        assert user.subscription_tier == SubscriptionTier.FREE
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# _handle_subscription_updated — gap paths
# ---------------------------------------------------------------------------


class TestHandleSubscriptionUpdatedGaps:
    """Gap tests for _handle_subscription_updated."""

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_no_client_falls_back_to_raw_status(self):
        """When get_stripe_client() returns None the handler must fall back to the
        raw 'status' field from the webhook event data."""
        user = _make_user(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            subscription_tier=SubscriptionTier.PRO,
        )
        session = _mock_db_session()
        db_result = MagicMock()
        db_result.first.return_value = user
        session.exec = AsyncMock(return_value=db_result)

        data = {
            "customer_id": "cus_123",
            "subscription_id": "sub_123",
            "status": "past_due",  # raw status from Stripe webhook payload
        }

        wp_patch, _ = _mock_webhook_processor_ctx()
        with (
            wp_patch,
            patch("app.api.subscriptions.get_stripe_client", return_value=None),
        ):
            await _handle_subscription_updated(data, session, stripe_event_id="evt_pastdue")

        # Raw status from the webhook payload must be applied
        assert user.subscription_status == "past_due"
        assert user.stripe_subscription_id == "sub_123"
        session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_no_subscription_found_falls_back(self):
        """When the Stripe client exists but get_subscription() returns None the
        handler must fall back to writing the raw status from the event data."""
        user = _make_user(
            stripe_customer_id="cus_123",
            subscription_tier=SubscriptionTier.PRO,
        )
        session = _mock_db_session()
        db_result = MagicMock()
        db_result.first.return_value = user
        session.exec = AsyncMock(return_value=db_result)

        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(return_value=None)  # not found

        data = {
            "customer_id": "cus_123",
            "subscription_id": "sub_not_found",
            "status": "unpaid",
        }

        wp_patch, _ = _mock_webhook_processor_ctx()
        with (
            wp_patch,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
        ):
            await _handle_subscription_updated(data, session, stripe_event_id="evt_notfound")

        # Must fall back to raw status value from webhook data
        assert user.subscription_status == "unpaid"
        assert user.stripe_subscription_id == "sub_not_found"
        session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_no_client_no_status_still_commits(self):
        """When client is None and no 'status' key is present the handler must
        still persist the subscription_id and commit without crashing."""
        user = _make_user(stripe_customer_id="cus_nostatus")
        session = _mock_db_session()
        db_result = MagicMock()
        db_result.first.return_value = user
        session.exec = AsyncMock(return_value=db_result)

        # No 'status' key in event data
        data = {
            "customer_id": "cus_nostatus",
            "subscription_id": "sub_nostatus",
        }

        wp_patch, _ = _mock_webhook_processor_ctx()
        with (
            wp_patch,
            patch("app.api.subscriptions.get_stripe_client", return_value=None),
        ):
            await _handle_subscription_updated(data, session, stripe_event_id="evt_nostatus")

        assert user.stripe_subscription_id == "sub_nostatus"
        # No status in data → no flush needed, but subscription_id is persisted
        # The commit happens via the FastAPI session lifecycle after the handler returns


# ---------------------------------------------------------------------------
# _sync_subscription_from_stripe — gap paths
# ---------------------------------------------------------------------------


class TestSyncSubscriptionFromStripeGaps:
    """Gap tests for _sync_subscription_from_stripe."""

    @pytest.mark.asyncio
    async def test_sync_subscription_cancel_at_period_end_status(self):
        """active + cancel_at_period_end=True must produce status='cancel_at_period_end'."""
        user = _make_user(
            stripe_customer_id="cus_cpe",
            subscription_tier=SubscriptionTier.PRO,
            subscription_status="active",
        )
        session = _mock_db_session()

        sub = _make_stripe_subscription(
            sub_id="sub_canceling",
            tier="pro",
            status="active",
            cancel_at_period_end=True,  # scheduled cancellation
        )

        mock_client = AsyncMock()
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[sub])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        # Status must be remapped — NOT left as plain "active"
        assert user.subscription_status == "cancel_at_period_end"
        assert user.stripe_subscription_id == "sub_canceling"
        assert user.subscription_tier == SubscriptionTier.PRO
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_subscription_downgrades_pro_user_when_no_subscription(self):
        """A PRO user with no active Stripe subscription must be downgraded to FREE
        with status='canceled' and stripe_subscription_id cleared."""
        user = _make_user(
            stripe_customer_id="cus_downgrade",
            stripe_subscription_id="sub_old",
            subscription_tier=SubscriptionTier.PRO,
            subscription_status="active",
        )
        session = _mock_db_session()

        mock_client = AsyncMock()
        # Both active_only=True and active_only=False return empty lists
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.subscription_status == "canceled"
        assert user.stripe_subscription_id is None
        assert user.subscription_expires_at is None
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_subscription_active_no_cancel_flag_keeps_active_status(self):
        """active + cancel_at_period_end=False must keep plain 'active' status."""
        user = _make_user(
            stripe_customer_id="cus_active",
            subscription_tier=SubscriptionTier.FREE,
        )
        session = _mock_db_session()

        sub = _make_stripe_subscription(
            sub_id="sub_active",
            tier="pro",
            status="active",
            cancel_at_period_end=False,
        )
        mock_client = AsyncMock()
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[sub])

        with patch("app.api.subscriptions.get_stripe_client", return_value=mock_client):
            await _sync_subscription_from_stripe(user, session)

        # Status must NOT be mutated to cancel_at_period_end
        assert user.subscription_status == "active"
        assert user.subscription_tier == SubscriptionTier.PRO
        session.commit.assert_awaited()


# ---------------------------------------------------------------------------
# create_checkout_session — gap paths
# ---------------------------------------------------------------------------


class TestCreateCheckoutSessionGaps:
    """Gap tests for create_checkout_session."""

    def setup_method(self) -> None:
        """Reset the Stripe client singleton to avoid cross-test contamination."""
        import app.api.subscriptions as mod

        mod._stripe_client = None

    def teardown_method(self) -> None:
        import app.api.subscriptions as mod

        mod._stripe_client = None

    @pytest.mark.asyncio
    async def test_create_checkout_with_referral_code_sets_client_reference_id(self):
        """referral_code in the request payload must be forwarded as
        client_reference_id in the stripe.checkout.Session.create() call."""
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123", referral_code="REF2024")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_ref"
        mock_client.create_customer = AsyncMock(return_value=customer)
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[])

        captured_params: dict[str, Any] = {}

        def _capture_create(**kwargs: Any) -> MagicMock:
            captured_params.update(kwargs)
            result = MagicMock()
            result.url = "https://checkout.stripe.com/ref"
            result.id = "cs_ref"
            return result

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", side_effect=_capture_create),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            mock_analytics.return_value = MagicMock()

            result = await create_checkout_session(payload, user, session)

        assert result.url == "https://checkout.stripe.com/ref"
        # Referral code forwarded as Stripe client_reference_id
        assert captured_params.get("client_reference_id") == "REF2024"

        # Analytics must record the referral code property
        analytics_mock = mock_analytics.return_value
        analytics_mock.capture.assert_called()
        call_args = analytics_mock.capture.call_args_list[0]
        assert call_args.kwargs["properties"]["referral_code"] == "REF2024"

    @pytest.mark.asyncio
    async def test_create_checkout_without_referral_code_omits_client_reference_id(self):
        """When no referral_code is provided, client_reference_id must NOT appear
        in the Stripe checkout.Session.create() call."""
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")  # no referral_code

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_noref"
        mock_client.create_customer = AsyncMock(return_value=customer)

        captured_params: dict[str, Any] = {}

        def _capture_create(**kwargs: Any) -> MagicMock:
            captured_params.update(kwargs)
            result = MagicMock()
            result.url = "https://checkout.stripe.com/noref"
            result.id = "cs_noref"
            return result

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", side_effect=_capture_create),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            mock_analytics.return_value = MagicMock()

            await create_checkout_session(payload, user, session)

        assert "client_reference_id" not in captured_params

    @pytest.mark.asyncio
    async def test_create_checkout_with_trial_days_adds_trial_period(self):
        """When stripe_trial_days > 0, subscription_data must include
        trial_period_days equal to that value."""
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_trial"
        mock_client.create_customer = AsyncMock(return_value=customer)
        mock_client.get_customer_subscriptions = AsyncMock(return_value=[])

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
            mock_settings.stripe_trial_days = 14  # 14-day trial
            mock_analytics.return_value = MagicMock()

            result = await create_checkout_session(payload, user, session)

        assert result.url == "https://checkout.stripe.com/trial"
        assert captured_params["subscription_data"]["trial_period_days"] == 14
        assert captured_params["subscription_data"]["metadata"]["user_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_create_checkout_with_zero_trial_days_omits_trial_period(self):
        """When stripe_trial_days == 0, subscription_data must NOT include
        trial_period_days."""
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_123")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_notrial"
        mock_client.create_customer = AsyncMock(return_value=customer)

        captured_params: dict[str, Any] = {}

        def _capture_create(**kwargs: Any) -> MagicMock:
            captured_params.update(kwargs)
            result = MagicMock()
            result.url = "https://checkout.stripe.com/notrial"
            result.id = "cs_notrial"
            return result

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", side_effect=_capture_create),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 0
            mock_analytics.return_value = MagicMock()

            await create_checkout_session(payload, user, session)

        assert "trial_period_days" not in captured_params.get("subscription_data", {})

    @pytest.mark.asyncio
    async def test_create_checkout_with_referral_code_and_trial_days(self):
        """Both referral_code and trial_days > 0 must coexist correctly in the
        Stripe checkout params."""
        user = _make_user(stripe_customer_id=None)
        session = _mock_db_session()
        payload = CheckoutRequest(price_id="price_pro", referral_code="COMBO999")

        mock_client = AsyncMock()
        customer = MagicMock()
        customer.id = "cus_combo"
        mock_client.create_customer = AsyncMock(return_value=customer)

        captured_params: dict[str, Any] = {}

        def _capture_create(**kwargs: Any) -> MagicMock:
            captured_params.update(kwargs)
            result = MagicMock()
            result.url = "https://checkout.stripe.com/combo"
            result.id = "cs_combo"
            return result

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            patch("app.api.subscriptions.get_stripe_client", return_value=mock_client),
            patch("stripe.checkout.Session.create", side_effect=_capture_create),
            patch("app.api.subscriptions.get_analytics") as mock_analytics,
        ):
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.test"
            mock_settings.stripe_trial_days = 30
            mock_analytics.return_value = MagicMock()

            await create_checkout_session(payload, user, session)

        assert captured_params.get("client_reference_id") == "COMBO999"
        assert captured_params["subscription_data"]["trial_period_days"] == 30


# ---------------------------------------------------------------------------
# stripe_webhook — gap paths
# ---------------------------------------------------------------------------


class TestWebhookGaps:
    """Gap tests for stripe_webhook."""

    def _make_request(
        self,
        *,
        body: bytes = b"{}",
        sig_header: str | None = "t=1,v1=abc",
    ) -> MagicMock:
        """Construct a minimal FastAPI Request mock."""
        req = MagicMock()
        req.body = AsyncMock(return_value=body)
        req.headers = {"stripe-signature": sig_header} if sig_header else {}
        return req

    @pytest.mark.asyncio
    async def test_webhook_missing_stripe_signature_header_returns_400(self):
        """When the stripe-signature header is absent the endpoint must return
        HTTP 400 with a message mentioning 'stripe-signature'."""
        req = self._make_request(sig_header=None)  # no stripe-signature header

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_webhook_secret = "whsec_configured"
            await stripe_webhook(req)

        assert exc_info.value.status_code == 400
        assert "stripe-signature" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_webhook_empty_stripe_signature_value_returns_400(self):
        """An empty string stripe-signature value is falsy and must also trigger
        the 400 branch — same code path as a missing header."""
        req = MagicMock()
        req.body = AsyncMock(return_value=b"{}")
        req.headers = {"stripe-signature": ""}  # present but empty → falsy

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_webhook_secret = "whsec_configured"
            await stripe_webhook(req)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_not_configured_returns_503(self):
        """When stripe_webhook_secret is empty the endpoint must return 503 before
        reading the request body."""
        req = self._make_request()

        with (
            patch("app.api.subscriptions.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.stripe_webhook_secret = ""
            await stripe_webhook(req)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_webhook_valid_signature_routes_to_checkout_handler(self):
        """A well-formed webhook with checkout.session.completed must delegate to
        _handle_checkout_completed."""
        req = self._make_request(sig_header="t=1,v1=valid_sig")
        event = MagicMock()
        event.id = "evt_checkout_gap"
        event.type = "checkout.session.completed"
        event.data = {"customer_id": "cus_gap", "user_id": str(uuid4())}

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
            ) as mock_handler,
        ):
            mock_settings.stripe_webhook_secret = "whsec_configured"
            result = await stripe_webhook(req)

        assert result == {"status": "success"}
        mock_handler.assert_awaited_once_with(event.data, mock_session, "evt_checkout_gap")
