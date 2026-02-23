"""Unit tests for app/dependencies.py — rate limiting and quota checking."""

import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.dependencies import EndpointRateLimiter, check_interview_quota
from app.models.user import SubscriptionTier


class TestEndpointRateLimiter:
    """Tests for the in-memory per-endpoint rate limiter."""

    def _make_request(self, path="/api/test", client_ip="1.2.3.4", headers=None):
        """Create a mock FastAPI Request."""
        req = MagicMock()
        req.url.path = path
        req.client.host = client_ip
        req.headers = headers or {}
        return req

    def test_allows_requests_within_limit(self):
        limiter = EndpointRateLimiter(max_requests=5, window_seconds=60)
        req = self._make_request()

        for _ in range(5):
            limiter.check(req)  # Should not raise

    def test_blocks_requests_over_limit(self):
        limiter = EndpointRateLimiter(max_requests=3, window_seconds=60)
        req = self._make_request()

        for _ in range(3):
            limiter.check(req)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check(req)

        assert exc_info.value.status_code == 429
        assert "Too many requests" in exc_info.value.detail

    def test_different_ips_have_separate_limits(self):
        limiter = EndpointRateLimiter(max_requests=2, window_seconds=60)

        req_a = self._make_request(client_ip="10.0.0.1")
        req_b = self._make_request(client_ip="10.0.0.2")

        for _ in range(2):
            limiter.check(req_a)
            limiter.check(req_b)

        # Both should now be at limit
        with pytest.raises(HTTPException):
            limiter.check(req_a)
        with pytest.raises(HTTPException):
            limiter.check(req_b)

    def test_different_paths_have_separate_limits(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=60)

        req_login = self._make_request(path="/api/login")
        req_register = self._make_request(path="/api/register")

        limiter.check(req_login)
        limiter.check(req_register)  # Different path, should not raise

        with pytest.raises(HTTPException):
            limiter.check(req_login)

    def test_window_expiry_allows_new_requests(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=1)
        req = self._make_request()

        limiter.check(req)

        with pytest.raises(HTTPException):
            limiter.check(req)

        # Simulate time passing beyond window
        limiter._requests[f"{req.url.path}:{req.client.host}"] = [time.time() - 2]

        limiter.check(req)  # Should pass after old entries expire

    def test_cloudflare_ip_extraction(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=60)

        req = self._make_request(headers={"CF-RAY": "abc123", "CF-Connecting-IP": "203.0.113.50"})

        ip = limiter._get_client_ip(req)
        assert ip == "203.0.113.50"

    def test_cloudflare_ip_requires_both_headers(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=60)

        # CF-RAY without CF-Connecting-IP — should fall through to client.host
        req = self._make_request(client_ip="10.0.0.1", headers={"CF-RAY": "abc123"})

        ip = limiter._get_client_ip(req)
        assert ip == "10.0.0.1"

    def test_xff_header_rightmost_ip(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=60)

        headers = {"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 3.3.3.3"}
        req = self._make_request(headers=headers)

        ip = limiter._get_client_ip(req)
        assert ip == "3.3.3.3"

    def test_xff_header_too_many_hops_falls_through(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=60)

        # More than 5 hops — suspicious, fall through to client.host
        headers = {"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 3.3.3.3, 4.4.4.4, 5.5.5.5, 6.6.6.6"}
        req = self._make_request(client_ip="9.9.9.9", headers=headers)

        ip = limiter._get_client_ip(req)
        assert ip == "9.9.9.9"

    def test_no_client_returns_unknown(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=60)

        req = self._make_request()
        req.client = None
        req.headers = {}

        ip = limiter._get_client_ip(req)
        assert ip == "unknown"

    def test_retry_after_header_on_429(self):
        limiter = EndpointRateLimiter(max_requests=1, window_seconds=42)
        req = self._make_request()

        limiter.check(req)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check(req)

        assert exc_info.value.headers["Retry-After"] == "42"


class TestCheckInterviewQuota:
    """Tests for the interview quota dependency."""

    def _make_user(
        self,
        tier=SubscriptionTier.FREE,
        interviews_this_month=0,
        interviews_reset_at=None,
        created_at=None,
    ):
        user = MagicMock()
        user.id = uuid4()
        user.subscription_tier = tier
        user.interviews_this_month = interviews_this_month
        user.interviews_reset_at = interviews_reset_at
        user.created_at = created_at or datetime.now(UTC)
        return user

    @pytest.mark.asyncio
    async def test_free_user_under_quota_passes(self):
        user = self._make_user(interviews_this_month=1)
        session = AsyncMock()

        with patch("app.dependencies.get_current_user", return_value=user):
            result = await check_interview_quota(current_user=user, session=session)

        assert result == user

    @pytest.mark.asyncio
    async def test_free_user_at_quota_blocked(self):
        user = self._make_user(interviews_this_month=3)
        session = AsyncMock()

        with (
            patch("app.dependencies.get_current_user", return_value=user),
            patch("app.config.settings") as mock_settings,
        ):
            mock_settings.stripe_price_id_pro_monthly = "price_123"
            mock_settings.stripe_secret_key = "sk_test"
            mock_settings.frontend_url = "https://app.codeswiftr.com"

            with pytest.raises(HTTPException) as exc_info:
                await check_interview_quota(current_user=user, session=session)

            assert exc_info.value.status_code == 402
            detail = exc_info.value.detail
            assert detail["interviews_used"] == 3
            assert detail["interviews_limit"] == 3
            assert "upgrade" in detail["upgrade_url"].lower()

    @pytest.mark.asyncio
    async def test_pro_user_unlimited(self):
        user = self._make_user(tier=SubscriptionTier.PRO, interviews_this_month=100)
        session = AsyncMock()

        result = await check_interview_quota(current_user=user, session=session)
        assert result == user

    @pytest.mark.asyncio
    async def test_monthly_reset_clears_counter(self):
        """Counter resets when we cross into a new month."""
        # User last reset in January
        user = self._make_user(
            interviews_this_month=3,
            interviews_reset_at=datetime(2026, 1, 15, tzinfo=UTC),
        )
        session = AsyncMock()

        # "Now" is February — should reset
        result = await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 0
        assert user.interviews_reset_at is not None
        session.commit.assert_called_once()
        assert result == user

    @pytest.mark.asyncio
    async def test_same_month_no_reset(self):
        """Counter should not reset within the same month."""
        now = datetime.now(UTC)
        user = self._make_user(
            interviews_this_month=2,
            interviews_reset_at=now.replace(day=1),
        )
        session = AsyncMock()

        result = await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 2
        session.commit.assert_not_called()
        assert result == user

    @pytest.mark.asyncio
    async def test_quota_detail_without_stripe(self):
        """When Stripe not configured, upgrade_url should be None."""
        user = self._make_user(interviews_this_month=3)
        session = AsyncMock()

        with patch("app.config.settings") as mock_settings:
            mock_settings.stripe_price_id_pro_monthly = None
            mock_settings.stripe_secret_key = None
            mock_settings.frontend_url = "https://app.codeswiftr.com"

            with pytest.raises(HTTPException) as exc_info:
                await check_interview_quota(current_user=user, session=session)

            detail = exc_info.value.detail
            assert detail["upgrade_url"] is None

    @pytest.mark.asyncio
    async def test_fallback_to_created_at_for_reset(self):
        """Users without interviews_reset_at fall back to created_at."""
        user = self._make_user(
            interviews_this_month=3,
            interviews_reset_at=None,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        session = AsyncMock()

        # January created_at vs February now → should reset
        result = await check_interview_quota(current_user=user, session=session)

        assert user.interviews_this_month == 0
        assert result == user


class TestRateLimitWrappers:
    """Tests for pre-configured rate limiter convenience functions."""

    def _make_request(self, path="/api/test", client_ip="1.2.3.4"):
        req = MagicMock()
        req.url.path = path
        req.client.host = client_ip
        req.headers = {}
        return req

    def test_rate_limit_login(self):
        from app.dependencies import rate_limit_login

        req = self._make_request()
        rate_limit_login(req)  # Should not raise

    def test_rate_limit_register(self):
        from app.dependencies import rate_limit_register

        req = self._make_request()
        rate_limit_register(req)  # Should not raise

    def test_rate_limit_password_reset(self):
        from app.dependencies import rate_limit_password_reset

        req = self._make_request()
        rate_limit_password_reset(req)  # Should not raise
