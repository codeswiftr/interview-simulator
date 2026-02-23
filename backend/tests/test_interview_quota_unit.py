"""Pure unit tests for check_interview_quota dependency.

Tests the monthly reset logic and quota enforcement.
No database required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.dependencies import check_interview_quota
from app.models.user import SubscriptionTier


def _make_user(
    tier=SubscriptionTier.FREE,
    interviews=0,
    created_at=None,
    reset_at=None,
):
    user = MagicMock()
    user.subscription_tier = tier
    user.interviews_this_month = interviews
    user.created_at = created_at or datetime.now(UTC)
    user.interviews_reset_at = reset_at
    user.id = "user-123"
    return user


class TestMonthlyReset:
    @pytest.mark.asyncio
    async def test_resets_counter_new_month(self):
        """Counter resets when current month differs from last reset month."""
        last_month = datetime(2026, 1, 15, tzinfo=UTC)
        user = _make_user(interviews=3, reset_at=last_month)
        session = AsyncMock()

        with patch("app.config.settings"):
            await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 0
        assert user.interviews_reset_at is not None
        assert user.interviews_reset_at.month == datetime.now(UTC).month
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_no_reset_same_month(self):
        """Counter does not reset within the same month."""
        this_month = datetime.now(UTC).replace(day=1)
        user = _make_user(interviews=2, reset_at=this_month)
        session = AsyncMock()

        with patch("app.config.settings"):
            await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 2

    @pytest.mark.asyncio
    async def test_fallback_to_created_at_when_no_reset_at(self):
        """Uses created_at when interviews_reset_at is None (legacy users)."""
        last_month = datetime(2026, 1, 10, tzinfo=UTC)
        user = _make_user(interviews=3, created_at=last_month, reset_at=None)
        session = AsyncMock()

        with patch("app.config.settings"):
            await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 0
        assert user.interviews_reset_at is not None

    @pytest.mark.asyncio
    async def test_no_reset_for_new_user_same_month(self):
        """A new user created this month should not have counter reset."""
        now = datetime.now(UTC)
        user = _make_user(interviews=1, created_at=now, reset_at=None)
        session = AsyncMock()

        with patch("app.config.settings"):
            await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 1


class TestQuotaEnforcement:
    @pytest.mark.asyncio
    async def test_free_user_under_limit_passes(self):
        """Free user with <3 interviews can proceed."""
        now = datetime.now(UTC)
        user = _make_user(interviews=2, reset_at=now)
        session = AsyncMock()

        with patch("app.config.settings"):
            result = await check_interview_quota(current_user=user, session=session)
        assert result is user

    @pytest.mark.asyncio
    async def test_free_user_at_limit_blocked(self):
        """Free user with >=3 interviews gets 402."""
        now = datetime.now(UTC)
        user = _make_user(interviews=3, reset_at=now)
        session = AsyncMock()

        with patch("app.config.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_123"
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.codeswiftr.com"

            with pytest.raises(HTTPException) as exc_info:
                await check_interview_quota(current_user=user, session=session)
            assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_pro_user_unlimited(self):
        """Pro user can always proceed."""
        now = datetime.now(UTC)
        user = _make_user(tier=SubscriptionTier.PRO, interviews=100, reset_at=now)
        session = AsyncMock()

        with patch("app.config.settings"):
            result = await check_interview_quota(current_user=user, session=session)
        assert result is user

    @pytest.mark.asyncio
    async def test_team_user_unlimited(self):
        """Team user can always proceed."""
        now = datetime.now(UTC)
        user = _make_user(tier=SubscriptionTier.TEAM, interviews=50, reset_at=now)
        session = AsyncMock()

        with patch("app.config.settings"):
            result = await check_interview_quota(current_user=user, session=session)
        assert result is user

    @pytest.mark.asyncio
    async def test_402_includes_upgrade_url(self):
        """402 response includes upgrade URL and price_id."""
        now = datetime.now(UTC)
        user = _make_user(interviews=3, reset_at=now)
        session = AsyncMock()

        with patch("app.config.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = "price_abc"
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.codeswiftr.com"

            with pytest.raises(HTTPException) as exc_info:
                await check_interview_quota(current_user=user, session=session)

            detail = exc_info.value.detail
            assert detail["price_id"] == "price_abc"
            assert "upgrade_url" in detail

    @pytest.mark.asyncio
    async def test_reset_then_allow(self):
        """Free user who was at limit last month can proceed after reset."""
        last_month = datetime(2026, 1, 20, tzinfo=UTC)
        user = _make_user(interviews=3, reset_at=last_month)
        session = AsyncMock()

        with patch("app.config.settings"):
            result = await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 0
        assert result is user
