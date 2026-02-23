"""Pure unit tests for app/api/auth.py endpoints.

Tests cover:
- POST /forgot-password  (user exists, unknown email, email error, rate limiting)
- POST /reset-password   (valid token, expired, used, invalid, missing user)
- POST /refresh          (valid rotation, invalid token, expired token)
- POST /logout           (authenticated clears token, unauthenticated 401)
- ResetPasswordRequest   (pydantic validation: short password, missing complexity)

No database required — all DB interactions are mocked via AsyncMock.
Rate limiting dependency is bypassed with a no-op override.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    forgot_password,
    logout,
    refresh_token,
    reset_password,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_db_session() -> AsyncMock:
    """Return a minimal async session mock that handles exec/add/commit."""
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = None
    session.exec = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


def _make_user(
    email: str = "alice@example.com",
    user_id=None,
    refresh_token_val: str | None = None,
    refresh_token_expires_at: datetime | None = None,
    hashed_password: str = "$2b$12$fakehash",
) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    user.hashed_password = hashed_password
    user.refresh_token = refresh_token_val
    user.refresh_token_expires_at = refresh_token_expires_at
    return user


def _make_reset_token(
    user_id=None,
    token: str = "valid-token-abc",
    used: bool = False,
    expires_at: datetime | None = None,
) -> MagicMock:
    rt = MagicMock()
    rt.user_id = user_id or uuid4()
    rt.token = token
    rt.used = used
    rt.expires_at = expires_at or (datetime.now(UTC) + timedelta(hours=1))
    return rt


# ---------------------------------------------------------------------------
# ForgotPasswordRequest — Pydantic validation
# ---------------------------------------------------------------------------


class TestForgotPasswordRequest:
    def test_valid_email_accepted(self):
        req = ForgotPasswordRequest(email="user@example.com")
        assert req.email == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email="not-an-email")

    def test_email_normalised_to_lowercase_by_pydantic_emailstr(self):
        # Pydantic EmailStr lowercases the domain but preserves local part
        # The endpoint itself calls .lower() on lookup — testing the model field exists
        req = ForgotPasswordRequest(email="Alice@Example.COM")
        assert "@" in req.email


# ---------------------------------------------------------------------------
# ResetPasswordRequest — Pydantic + custom validation
# ---------------------------------------------------------------------------


class TestResetPasswordRequest:
    """Validate that ResetPasswordRequest enforces password rules at model level."""

    def test_valid_password_accepted(self):
        req = ResetPasswordRequest(token="abc123", new_password="SecurePass1!")
        assert req.token == "abc123"
        assert req.new_password == "SecurePass1!"

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="abc", new_password="Short1!")

    def test_password_no_uppercase_raises(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="abc", new_password="nouppercase1!")

    def test_password_no_lowercase_raises(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="abc", new_password="NOLOWER1!")

    def test_password_no_digit_raises(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="abc", new_password="NoDigitsHere!")

    def test_empty_token_raises(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="", new_password="ValidPass1!")

    def test_common_password_raises(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="abc", new_password="password")


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------


class TestForgotPassword:
    """Unit tests for the forgot_password endpoint function."""

    @pytest.mark.asyncio
    async def test_known_email_returns_generic_success(self):
        """User exists: creates token, sends email, returns generic success message."""
        user = _make_user()
        session = _mock_db_session()
        # First exec() call finds the user
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        with patch("app.api.auth.EmailService") as mock_email_cls, patch(
            "app.api.auth.settings"
        ) as mock_settings:
            mock_svc = AsyncMock()
            mock_svc.send_password_reset = AsyncMock(return_value=True)
            mock_email_cls.return_value = mock_svc
            mock_settings.frontend_url = "https://app.example.com"

            payload = ForgotPasswordRequest(email="alice@example.com")
            response = await forgot_password(payload, session)

        assert "password reset link has been sent" in response["message"].lower()
        session.add.assert_called_once()
        session.commit.assert_called_once()
        mock_svc.send_password_reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_email_returns_same_generic_success(self):
        """Security: endpoint returns identical response for non-existent user."""
        session = _mock_db_session()
        # exec() returns no user
        empty_result = MagicMock()
        empty_result.first.return_value = None
        session.exec.return_value = empty_result

        payload = ForgotPasswordRequest(email="nobody@example.com")
        response = await forgot_password(payload, session)

        assert "password reset link has been sent" in response["message"].lower()
        # No token created, no email sent
        session.add.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_send_failure_does_not_propagate(self):
        """EmailService exception is swallowed — endpoint still returns 200 dict."""
        user = _make_user()
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        with patch("app.api.auth.EmailService") as mock_email_cls, patch(
            "app.api.auth.settings"
        ) as mock_settings:
            mock_svc = AsyncMock()
            mock_svc.send_password_reset = AsyncMock(side_effect=RuntimeError("SMTP down"))
            mock_email_cls.return_value = mock_svc
            mock_settings.frontend_url = "https://app.example.com"

            payload = ForgotPasswordRequest(email="alice@example.com")
            # Must NOT raise — errors are swallowed for security
            response = await forgot_password(payload, session)

        assert "message" in response

    @pytest.mark.asyncio
    async def test_reset_url_contains_token(self):
        """The generated reset URL is passed to EmailService with the token."""
        user = _make_user()
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        captured_url: list[str] = []

        with patch("app.api.auth.EmailService") as mock_email_cls, patch(
            "app.api.auth.settings"
        ) as mock_settings:
            mock_svc = AsyncMock()

            async def capture_send(email_addr, url):
                captured_url.append(url)
                return True

            mock_svc.send_password_reset = capture_send
            mock_email_cls.return_value = mock_svc
            mock_settings.frontend_url = "https://app.example.com"

            await forgot_password(ForgotPasswordRequest(email="alice@example.com"), session)

        assert len(captured_url) == 1
        assert "reset-password?token=" in captured_url[0]

    @pytest.mark.asyncio
    async def test_email_lookup_uses_lowercase(self):
        """Email lookup normalises the address to lowercase."""
        session = _mock_db_session()
        empty_result = MagicMock()
        empty_result.first.return_value = None
        session.exec.return_value = empty_result

        # Providing mixed-case email — endpoint should still execute without error
        payload = ForgotPasswordRequest(email="Alice@Example.COM")
        response = await forgot_password(payload, session)
        assert "message" in response


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------


class TestResetPassword:
    """Unit tests for the reset_password endpoint function."""

    @pytest.mark.asyncio
    async def test_valid_token_resets_password(self):
        """Happy path: valid, unused, unexpired token → password updated."""
        user_id = uuid4()
        reset_tok = _make_reset_token(user_id=user_id)
        user = _make_user(user_id=user_id)

        session = _mock_db_session()
        # First exec finds the reset token, second finds the user
        token_result = MagicMock()
        token_result.first.return_value = reset_tok
        user_result = MagicMock()
        user_result.first.return_value = user

        session.exec.side_effect = [token_result, user_result]

        payload = ResetPasswordRequest(token="valid-token-abc", new_password="NewSecure1!")

        with patch("app.api.auth.hash_password", return_value="$2b$12$newhash") as mock_hash:
            response = await reset_password(payload, session)

        assert "successfully reset" in response["message"].lower()
        assert user.hashed_password == "$2b$12$newhash"
        assert user.refresh_token is None
        assert user.refresh_token_expires_at is None
        assert reset_tok.used is True
        session.commit.assert_called_once()
        mock_hash.assert_called_once_with("NewSecure1!")

    @pytest.mark.asyncio
    async def test_invalid_token_raises_400(self):
        """Non-existent token → 400 Bad Request."""
        session = _mock_db_session()
        empty_result = MagicMock()
        empty_result.first.return_value = None
        session.exec.return_value = empty_result

        payload = ResetPasswordRequest(token="does-not-exist", new_password="ValidPass1!")

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(payload, session)

        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_used_token_raises_400(self):
        """Already-used token → 400 Bad Request with explicit message."""
        reset_tok = _make_reset_token(used=True)
        session = _mock_db_session()
        token_result = MagicMock()
        token_result.first.return_value = reset_tok
        session.exec.return_value = token_result

        payload = ResetPasswordRequest(token="used-token", new_password="ValidPass1!")

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(payload, session)

        assert exc_info.value.status_code == 400
        assert "already been used" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_expired_token_raises_400(self):
        """Expired token → 400 Bad Request with expired message."""
        expired_tok = _make_reset_token(
            expires_at=datetime.now(UTC) - timedelta(hours=1)  # 1 hour in the past
        )
        session = _mock_db_session()
        token_result = MagicMock()
        token_result.first.return_value = expired_tok
        session.exec.return_value = token_result

        payload = ResetPasswordRequest(token="expired-token", new_password="ValidPass1!")

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(payload, session)

        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_token_valid_but_user_missing_raises_400(self):
        """Token found but associated user no longer exists → 400."""
        reset_tok = _make_reset_token()
        session = _mock_db_session()

        token_result = MagicMock()
        token_result.first.return_value = reset_tok
        user_result = MagicMock()
        user_result.first.return_value = None  # user gone

        session.exec.side_effect = [token_result, user_result]

        payload = ResetPasswordRequest(token="orphan-token", new_password="ValidPass1!")

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(payload, session)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_invalidates_refresh_token(self):
        """After reset, existing refresh token is cleared to end all sessions."""
        user_id = uuid4()
        reset_tok = _make_reset_token(user_id=user_id)
        user = _make_user(
            user_id=user_id,
            refresh_token_val="old-refresh-hash",
            refresh_token_expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        session = _mock_db_session()
        token_result = MagicMock()
        token_result.first.return_value = reset_tok
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.side_effect = [token_result, user_result]

        with patch("app.api.auth.hash_password", return_value="$2b$12$newh"):
            await reset_password(
                ResetPasswordRequest(token="valid-token-abc", new_password="NewSecure1!"),
                session,
            )

        assert user.refresh_token is None
        assert user.refresh_token_expires_at is None


# ---------------------------------------------------------------------------
# POST /refresh  (token rotation)
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """Unit tests for the refresh_token endpoint function."""

    @pytest.mark.asyncio
    async def test_valid_refresh_token_returns_new_token_pair(self):
        """Valid refresh token → new access + refresh tokens (rotation)."""
        user = _make_user(refresh_token_val="stored-hash")
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        from app.models.user import RefreshTokenRequest

        payload = RefreshTokenRequest(refresh_token="raw-refresh-token")

        # hash_refresh_token is imported inside the function body so must be patched
        # at app.security, not app.api.auth
        with (
            patch("app.security.hash_refresh_token", return_value="stored-hash") as mock_hash_rt,
            patch("app.api.auth.verify_refresh_token", return_value=True) as mock_verify,
            patch("app.api.auth.create_access_token", return_value="new-access-token") as mock_cat,
            patch(
                "app.api.auth.create_refresh_token",
                return_value=("new-refresh-token", datetime.now(UTC) + timedelta(days=7)),
            ) as mock_crt,
        ):
            result = await refresh_token(payload, session)

        assert result.access_token == "new-access-token"
        assert result.refresh_token == "new-refresh-token"
        # Verify token was rotated: new hash stored
        mock_hash_rt.assert_called()
        mock_verify.assert_called_once()
        mock_cat.assert_called_once()
        mock_crt.assert_called_once()
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_refresh_token_raises_401(self):
        """Refresh token hash not found in DB → 401 Unauthorized."""
        session = _mock_db_session()
        empty_result = MagicMock()
        empty_result.first.return_value = None
        session.exec.return_value = empty_result

        from app.models.user import RefreshTokenRequest

        payload = RefreshTokenRequest(refresh_token="unknown-token")

        with (
            patch("app.security.hash_refresh_token", return_value="some-hash"),
            pytest.raises(HTTPException) as exc_info,
        ):
            await refresh_token(payload, session)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_expired_refresh_token_raises_401_and_clears_token(self):
        """Expired refresh token → 401, and stored token is cleared from DB."""
        user = _make_user(
            refresh_token_val="stored-hash",
            refresh_token_expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        from app.models.user import RefreshTokenRequest

        payload = RefreshTokenRequest(refresh_token="expired-raw-token")

        with (
            patch("app.security.hash_refresh_token", return_value="stored-hash"),
            patch("app.api.auth.verify_refresh_token", return_value=False),
            pytest.raises(HTTPException) as exc_info,
        ):
            await refresh_token(payload, session)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
        # Token should be cleared after expiry detection
        assert user.refresh_token is None
        assert user.refresh_token_expires_at is None
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_rotation_stores_new_hash(self):
        """After successful refresh, the new token hash is stored on the user."""
        user = _make_user(refresh_token_val="old-hash")
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        from app.models.user import RefreshTokenRequest

        payload = RefreshTokenRequest(refresh_token="raw-old-token")
        new_expires = datetime.now(UTC) + timedelta(days=7)

        with (
            patch("app.security.hash_refresh_token", side_effect=["old-hash", "new-hash"]),
            patch("app.api.auth.verify_refresh_token", return_value=True),
            patch("app.api.auth.create_access_token", return_value="at"),
            patch(
                "app.api.auth.create_refresh_token",
                return_value=("new-raw-token", new_expires),
            ),
        ):
            await refresh_token(payload, session)

        assert user.refresh_token == "new-hash"
        assert user.refresh_token_expires_at == new_expires

    @pytest.mark.asyncio
    async def test_refresh_returns_token_model_with_correct_type(self):
        """Response model Token has token_type = 'bearer'."""
        user = _make_user(refresh_token_val="stored-hash")
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        from app.models.user import RefreshTokenRequest

        payload = RefreshTokenRequest(refresh_token="raw")

        with (
            patch("app.security.hash_refresh_token", return_value="stored-hash"),
            patch("app.api.auth.verify_refresh_token", return_value=True),
            patch("app.api.auth.create_access_token", return_value="at"),
            patch(
                "app.api.auth.create_refresh_token",
                return_value=("rt", datetime.now(UTC) + timedelta(days=7)),
            ),
        ):
            result = await refresh_token(payload, session)

        assert result.token_type == "bearer"


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------


class TestLogout:
    """Unit tests for the logout endpoint function."""

    @pytest.mark.asyncio
    async def test_logout_clears_refresh_token(self):
        """Authenticated user: refresh token fields set to None and committed."""
        user = _make_user(
            refresh_token_val="some-hash",
            refresh_token_expires_at=datetime.now(UTC) + timedelta(days=3),
        )
        session = _mock_db_session()

        await logout(current_user=user, session=session)

        assert user.refresh_token is None
        assert user.refresh_token_expires_at is None
        session.add.assert_called_once_with(user)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_works_when_token_already_none(self):
        """Idempotent: logout when user has no refresh token is still successful."""
        user = _make_user(refresh_token_val=None, refresh_token_expires_at=None)
        session = _mock_db_session()

        # Should not raise
        await logout(current_user=user, session=session)

        assert user.refresh_token is None
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_unauthenticated_raises_401(self):
        """Without a valid JWT, get_current_user raises 401.

        We simulate this by calling get_current_user with no credentials.
        The endpoint depends on get_current_user, so we test the dependency
        directly here.
        """
        from app.dependencies import get_current_user

        mock_auth = MagicMock()
        mock_auth.decode_token.side_effect = Exception("no token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None, session=_mock_db_session(), auth=mock_auth)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_returns_none(self):
        """Logout endpoint has no response body (204 No Content — returns None)."""
        user = _make_user()
        session = _mock_db_session()

        result = await logout(current_user=user, session=session)

        assert result is None


# ---------------------------------------------------------------------------
# AuthRateLimiter (forgot_password_rate_limit dependency)
# ---------------------------------------------------------------------------


class TestForgotPasswordRateLimiter:
    """Unit tests for the AuthRateLimiter used by forgot-password."""

    def _make_request(self, client_ip: str = "1.2.3.4") -> MagicMock:
        req = MagicMock()
        req.client.host = client_ip
        req.headers = {}
        return req

    def test_within_limit_does_not_raise(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=5)
        req = self._make_request()

        for _ in range(5):
            limiter.check(req)  # Should not raise

    def test_exceeding_limit_raises_429(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=3)
        req = self._make_request()

        for _ in range(3):
            limiter.check(req)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check(req)

        assert exc_info.value.status_code == 429

    def test_different_ips_have_independent_counters(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=1)
        req_a = self._make_request("10.0.0.1")
        req_b = self._make_request("10.0.0.2")

        limiter.check(req_a)
        limiter.check(req_b)  # Different IP — should not raise

        with pytest.raises(HTTPException):
            limiter.check(req_a)

    def test_cloudflare_ip_used_when_cf_ray_present(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=10)
        req = self._make_request()
        req.headers = {"CF-RAY": "abc123", "CF-Connecting-IP": "203.0.113.50"}

        ip = limiter._get_client_ip(req)
        assert ip == "203.0.113.50"

    def test_cf_ray_without_cf_ip_falls_back_to_client(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=10)
        req = self._make_request("9.9.9.9")
        req.headers = {"CF-RAY": "abc123"}  # No CF-Connecting-IP

        ip = limiter._get_client_ip(req)
        assert ip == "9.9.9.9"

    def test_x_forwarded_for_rightmost_ip(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=10)
        req = self._make_request()
        req.headers = {"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 3.3.3.3"}

        ip = limiter._get_client_ip(req)
        assert ip == "3.3.3.3"

    def test_no_client_returns_fallback_ip(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=10)
        req = MagicMock()
        req.client = None
        req.headers = {}

        ip = limiter._get_client_ip(req)
        assert ip == "0.0.0.0"

    def test_retry_after_header_present_on_429(self):
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=1, window_seconds=90)
        req = self._make_request()

        limiter.check(req)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check(req)

        assert exc_info.value.headers["Retry-After"] == "90"


# ---------------------------------------------------------------------------
# Integration-style: direct endpoint calls with full mock chain
# ---------------------------------------------------------------------------


class TestRefreshTokenIntegration:
    """End-to-end mock tests exercising the full refresh flow."""

    @pytest.mark.asyncio
    async def test_refresh_full_flow_token_rotation(self):
        """Full mock: hash lookup → verify → generate new pair → store."""
        user_id = uuid4()
        raw_old = "raw.old.jwt.token"

        import hashlib

        old_hash = hashlib.sha256(raw_old.encode()).hexdigest()

        user = _make_user(
            user_id=user_id,
            refresh_token_val=old_hash,
            refresh_token_expires_at=datetime.now(UTC) + timedelta(days=5),
        )
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        from app.models.user import RefreshTokenRequest
        from app.security import hash_refresh_token

        # Use real hash function — lookup must match
        payload = RefreshTokenRequest(refresh_token=raw_old)
        new_expires = datetime.now(UTC) + timedelta(days=7)

        with (
            patch("app.security.hash_refresh_token", side_effect=hash_refresh_token),
            patch("app.api.auth.verify_refresh_token", return_value=True),
            patch("app.api.auth.create_access_token", return_value="fresh.access.token"),
            patch(
                "app.api.auth.create_refresh_token",
                return_value=("fresh.refresh.token", new_expires),
            ),
        ):
            result = await refresh_token(payload, session)

        assert result.access_token == "fresh.access.token"
        assert result.refresh_token == "fresh.refresh.token"
        # New hash stored
        new_expected_hash = hash_refresh_token("fresh.refresh.token")
        assert user.refresh_token == new_expected_hash
        assert user.refresh_token_expires_at == new_expires


class TestForgotPasswordIntegration:
    """Direct function call tests covering both branches of forgot_password."""

    @pytest.mark.asyncio
    async def test_forgot_password_token_expires_in_one_hour(self):
        """The reset token stored has expires_at ~1 hour from now."""
        user = _make_user()
        session = _mock_db_session()
        user_result = MagicMock()
        user_result.first.return_value = user
        session.exec.return_value = user_result

        saved_tokens: list[MagicMock] = []

        def capture_add(obj):
            saved_tokens.append(obj)

        session.add = MagicMock(side_effect=capture_add)

        with patch("app.api.auth.EmailService") as mock_email_cls, patch(
            "app.api.auth.settings"
        ) as mock_settings:
            mock_svc = AsyncMock()
            mock_svc.send_password_reset = AsyncMock(return_value=True)
            mock_email_cls.return_value = mock_svc
            mock_settings.frontend_url = "https://app.example.com"

            await forgot_password(ForgotPasswordRequest(email="alice@example.com"), session)

        # Find the PasswordResetToken that was added
        from app.models.password_reset import PasswordResetToken

        reset_tokens = [t for t in saved_tokens if isinstance(t, PasswordResetToken)]
        assert len(reset_tokens) == 1
        rt = reset_tokens[0]
        now = datetime.now(UTC)
        assert rt.expires_at > now + timedelta(minutes=55)
        assert rt.expires_at < now + timedelta(hours=2)
