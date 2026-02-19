"""Security hardening tests for Sprint 9 P0.

Tests for:
1. Input validation (Pydantic strict mode / constraints)
2. SQL injection prevention (parameterized queries)
3. CORS configuration tightening
4. Rate limiting on auth endpoints (login: 10/min, register: 5/min)
5. Security headers (HSTS, X-Content-Type-Options, X-Frame-Options)
"""

import time
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

# ============================================================
# 1. Input Validation Tests
# ============================================================

class TestInputValidation:
    """Test Pydantic strict input validation on request schemas."""

    def test_user_create_rejects_invalid_email(self):
        """UserCreate rejects malformed email addresses."""
        from app.models.user import UserCreate

        invalid_emails = [
            "not-an-email",
            "@missing-local.com",
            "missing-domain@",
            "spaces in@email.com",
            "",
        ]
        for email in invalid_emails:
            with pytest.raises((ValidationError, ValueError)):
                UserCreate(email=email, password="ValidPass123!")

    def test_user_create_rejects_email_without_domain(self):
        """Test UserCreate rejects emails without domain."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(email="user@", password="ValidPass123!")

    def test_user_create_accepts_valid_email(self):
        """UserCreate accepts properly formatted email addresses."""
        from app.models.user import UserCreate

        user = UserCreate(email="valid@example.com", password="Secret25")
        assert user.email == "valid@example.com"

    def test_user_create_rejects_short_password(self):
        """UserCreate rejects passwords shorter than 8 characters."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(email="test@example.com", password="short")

    def test_user_create_rejects_long_password(self):
        """UserCreate rejects passwords longer than 128 characters."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(email="test@example.com", password="a" * 129)

    def test_user_create_name_max_length(self):
        """UserCreate rejects full_name longer than 200 characters."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(
                email="test@example.com",
                password="Secret25",
                full_name="A" * 201,
            )

    def test_user_create_full_name_at_limit(self):
        """Test UserCreate accepts full_name at exactly 200 chars."""
        from app.models.user import UserCreate

        user = UserCreate(
            email="valid@example.com",
            password="ValidPass123!",
            full_name="A" * 200,
        )
        assert len(user.full_name) == 200

    def test_user_create_rejects_int_email(self):
        """Test strict mode rejects non-string email."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(email=12345, password="ValidPass123!")

    def test_user_create_rejects_int_password(self):
        """Test strict mode rejects non-string password."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(email="valid@example.com", password=12345)

    def test_user_login_rejects_invalid_email(self):
        """UserLogin rejects malformed email addresses."""
        from app.models.user import UserLogin

        with pytest.raises((ValidationError, ValueError)):
            UserLogin(email="not-an-email", password="anything")

    def test_user_login_strict_mode(self):
        """Test UserLogin strict mode rejects non-string types."""
        from app.models.user import UserLogin

        with pytest.raises((ValidationError, ValueError)):
            UserLogin(email=123, password="password")

    def test_user_login_rejects_empty_password(self):
        """UserLogin rejects empty password."""
        from app.models.user import UserLogin

        with pytest.raises((ValidationError, ValueError)):
            UserLogin(email="test@example.com", password="")

    def test_user_login_rejects_oversized_password(self):
        """UserLogin rejects password over 128 characters (brute force mitigation)."""
        from app.models.user import UserLogin

        with pytest.raises((ValidationError, ValueError)):
            UserLogin(email="test@example.com", password="a" * 129)

    def test_user_update_rejects_invalid_email(self):
        """UserUpdate rejects malformed email when provided."""
        from app.models.user import UserUpdate

        with pytest.raises((ValidationError, ValueError)):
            UserUpdate(email="not-valid-email")

    def test_user_update_accepts_none_email(self):
        """Test UserUpdate accepts None email (optional field)."""
        from app.models.user import UserUpdate

        update = UserUpdate(full_name="Test Name")
        assert update.email is None

    def test_user_update_name_max_length(self):
        """UserUpdate rejects full_name longer than 200 characters."""
        from app.models.user import UserUpdate

        with pytest.raises((ValidationError, ValueError)):
            UserUpdate(full_name="X" * 201)

    def test_user_update_full_name_max_length(self):
        """Test UserUpdate enforces full_name max_length=200."""
        from app.models.user import UserUpdate

        with pytest.raises((ValidationError, ValueError)):
            UserUpdate(full_name="A" * 201)

    def test_password_change_rejects_short_new_password(self):
        """PasswordChange rejects new_password shorter than 8 characters."""
        from app.models.user import PasswordChange

        with pytest.raises((ValidationError, ValueError)):
            PasswordChange(current_password="oldpass1", new_password="short")

    def test_password_change_strict_mode(self):
        """Test PasswordChange strict mode rejects non-string types."""
        from app.models.user import PasswordChange

        with pytest.raises((ValidationError, ValueError)):
            PasswordChange(current_password=123, new_password="ValidPass123!")

    def test_refresh_token_request_rejects_empty_token(self):
        """RefreshTokenRequest rejects empty token."""
        from app.models.user import RefreshTokenRequest

        with pytest.raises((ValidationError, ValueError)):
            RefreshTokenRequest(refresh_token="")

    def test_refresh_token_request_rejects_oversized_token(self):
        """RefreshTokenRequest rejects token over 512 characters."""
        from app.models.user import RefreshTokenRequest

        with pytest.raises((ValidationError, ValueError)):
            RefreshTokenRequest(refresh_token="x" * 513)

    def test_refresh_token_strict_mode(self):
        """Test RefreshTokenRequest strict mode rejects non-string types."""
        from app.models.user import RefreshTokenRequest

        with pytest.raises((ValidationError, ValueError)):
            RefreshTokenRequest(refresh_token=12345)

    def test_forgot_password_rejects_invalid_email(self):
        """ForgotPasswordRequest rejects malformed email."""
        from app.api.auth import ForgotPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ForgotPasswordRequest(email="not-an-email")

    def test_forgot_password_strict_mode(self):
        """Test ForgotPasswordRequest strict mode rejects non-string types."""
        from app.api.auth import ForgotPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ForgotPasswordRequest(email=12345)

    def test_reset_password_rejects_empty_token(self):
        """ResetPasswordRequest rejects empty token."""
        from app.api.auth import ResetPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ResetPasswordRequest(token="", new_password="Secret25")

    def test_reset_password_rejects_oversized_token(self):
        """ResetPasswordRequest rejects token over 512 characters."""
        from app.api.auth import ResetPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ResetPasswordRequest(token="x" * 513, new_password="Secret25")

    def test_reset_password_token_max_length(self):
        """Test ResetPasswordRequest token max_length=512."""
        from app.api.auth import ResetPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ResetPasswordRequest(
                token="A" * 513,
                new_password="ValidPass123!",
            )

    def test_reset_password_password_max_length(self):
        """Test ResetPasswordRequest new_password max_length=128."""
        from app.api.auth import ResetPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ResetPasswordRequest(
                token="valid-token",
                new_password="A" * 129,
            )

    def test_coaching_hint_request_rejects_invalid_question_type(self):
        """CoachingHintRequest only accepts valid question types."""
        from app.api.coaching import CoachingHintRequest

        with pytest.raises(ValidationError):
            CoachingHintRequest(
                question="Test question",
                question_type="invalid_type",
                transcript="",
            )

    def test_coaching_hint_request_accepts_valid_types(self):
        """CoachingHintRequest accepts behavioral, technical, system_design."""
        from app.api.coaching import CoachingHintRequest

        for qt in ["behavioral", "technical", "system_design"]:
            req = CoachingHintRequest(
                question="Test question", question_type=qt, transcript=""
            )
            assert req.question_type == qt

    def test_coaching_hint_request_rejects_oversized_transcript(self):
        """CoachingHintRequest rejects transcript over 50000 characters."""
        from app.api.coaching import CoachingHintRequest

        with pytest.raises(ValidationError):
            CoachingHintRequest(
                question="Test question",
                question_type="behavioral",
                transcript="x" * 50001,
            )


# ============================================================
# 2. SQL Injection Prevention Tests
# ============================================================

class TestSQLInjectionPrevention:
    """Verify that SQL injection payloads are safely handled."""

    def test_user_create_sql_injection_in_email(self):
        """SQL injection in email is caught by email validation."""
        from app.models.user import UserCreate

        with pytest.raises((ValidationError, ValueError)):
            UserCreate(
                email="' OR '1'='1'; DROP TABLE users; --",
                password="Secret25",
            )

    def test_user_login_sql_injection_in_email(self):
        """SQL injection in login email is caught by email validation."""
        from app.models.user import UserLogin

        with pytest.raises((ValidationError, ValueError)):
            UserLogin(
                email="admin' OR '1'='1'--",
                password="anything",
            )

    def test_forgot_password_sql_injection_in_email(self):
        """SQL injection in forgot-password email is caught by validation."""
        from app.api.auth import ForgotPasswordRequest

        with pytest.raises((ValidationError, ValueError)):
            ForgotPasswordRequest(email="'; DROP TABLE password_reset_tokens;--")


# ============================================================
# 3. CORS Configuration Tests
# ============================================================

class TestCORSConfiguration:
    """Test CORS origin restrictions."""

    def test_production_cors_origins_are_restricted(self):
        """Production CORS origins only include expected domains."""
        from app.config import Settings

        # Create a production-like settings instance with explicit origins
        settings = Settings(
            debug=False,
            environment="production",
            cors_origins=[
                "https://app.codeswiftr.com",
                "https://interview-simulator-4bo.pages.dev",
            ],
            _env_file=None,
        )
        origins = settings.effective_cors_origins

        # Should only contain production domains
        assert "https://app.codeswiftr.com" in origins
        assert "https://interview-simulator-4bo.pages.dev" in origins

        # Should NOT contain localhost in production
        assert "http://localhost:3000" not in origins
        assert "http://localhost:5173" not in origins

    def test_development_cors_includes_localhost(self):
        """Development CORS includes localhost origins."""
        from app.config import Settings

        settings = Settings(debug=True, _env_file=None)
        origins = settings.effective_cors_origins

        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins

    def test_no_wildcard_cors_origins(self):
        """CORS origins never include wildcards."""
        from app.config import Settings

        for env in ["development", "production"]:
            settings = Settings(
                debug=(env == "development"),
                environment=env,
                _env_file=None,
            )
            origins = settings.effective_cors_origins
            assert "*" not in origins
            assert "http://*" not in origins
            assert "https://*" not in origins

    @pytest.mark.asyncio
    async def test_cors_rejects_malicious_origin(self, client):
        """CORS preflight rejects unauthorized origins."""
        response = await client.options(
            "/api/v1/users/login",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Should not include Access-Control-Allow-Origin for malicious origin
        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        assert allow_origin != "https://evil.com"


class TestCORSHardening:
    """Test CORS configuration is secure."""

    @pytest.mark.asyncio
    async def test_cors_rejects_malicious_origin(self, client, db_session):
        """Test CORS rejects unauthorized origins."""
        resp = await client.options(
            "/api/v1/users/login",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "https://evil.com"

    @pytest.mark.asyncio
    async def test_cors_no_wildcard_origin(self, client, db_session):
        """Test CORS never returns wildcard origin."""
        resp = await client.options(
            "/api/v1/users/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "*"


# ============================================================
# 4. Auth Rate Limiting Tests
# ============================================================

class TestAuthRateLimiting:
    """Test per-endpoint rate limiting on auth endpoints."""

    def test_login_rate_limit_allows_under_threshold(self):
        """Login rate limiter allows up to 10 requests per minute."""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=10)
        request = self._make_request("192.168.1.1")

        # Should allow 10 requests
        for _ in range(10):
            limiter.check(request)  # Should not raise

    def test_login_rate_limit_blocks_over_threshold(self):
        """Login rate limiter blocks after 10 requests per minute."""
        from fastapi import HTTPException

        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=10)
        request = self._make_request("192.168.1.2")

        # Use up the limit
        for _ in range(10):
            limiter.check(request)

        # 11th request should be blocked
        with pytest.raises(HTTPException) as exc_info:
            limiter.check(request)
        assert exc_info.value.status_code == 429

    def test_register_rate_limit_blocks_after_5(self):
        """Register rate limiter blocks after 5 requests per minute."""
        from fastapi import HTTPException

        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=5)
        request = self._make_request("192.168.1.3")

        for _ in range(5):
            limiter.check(request)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check(request)
        assert exc_info.value.status_code == 429

    def test_rate_limit_per_ip_isolation(self):
        """Rate limits are tracked per IP address."""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=2)

        # IP 1 uses up its limit
        req1 = self._make_request("10.0.0.1")
        limiter.check(req1)
        limiter.check(req1)

        # IP 2 should still be allowed
        req2 = self._make_request("10.0.0.2")
        limiter.check(req2)  # Should not raise

    def test_rate_limit_window_expiry(self):
        """Rate limit counters reset after window expires."""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=2, window_seconds=1)
        request = self._make_request("10.0.0.3")

        # Use up limit
        limiter.check(request)
        limiter.check(request)

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        limiter.check(request)  # Should not raise

    def test_rate_limit_uses_cloudflare_ip_when_available(self):
        """Rate limiter extracts client IP from CF-Connecting-IP when CF-RAY present."""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=1)

        # Request with Cloudflare headers
        cf_request = self._make_request(
            "127.0.0.1",
            headers={
                "CF-RAY": "abc123",
                "CF-Connecting-IP": "203.0.113.50",
            },
        )
        limiter.check(cf_request)

        # Same CF IP should be rate limited
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            limiter.check(cf_request)

        # Different direct IP but no CF headers should still work
        direct_request = self._make_request("127.0.0.2")
        limiter.check(direct_request)  # Should not raise

    def test_rate_limit_429_includes_retry_after(self):
        """429 response includes Retry-After header."""
        from fastapi import HTTPException

        from app.middleware.auth_rate_limit import AuthRateLimiter

        limiter = AuthRateLimiter(requests_per_minute=1)
        request = self._make_request("10.0.0.4")
        limiter.check(request)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check(request)
        assert "Retry-After" in exc_info.value.headers

    @staticmethod
    def _make_request(ip: str, headers: dict | None = None) -> MagicMock:
        """Create a mock FastAPI request with the given client IP."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = ip
        request.headers = headers or {}
        return request


# ============================================================
# 5. API-level Input Validation Tests
# ============================================================

class TestInputValidationAPI:
    """Test input validation at the API level."""

    @pytest.mark.asyncio
    async def test_register_rejects_invalid_email(self, client, db_session):
        """Test /register rejects invalid email format via API."""
        resp = await client.post(
            "/api/v1/users/register",
            json={"email": "not-an-email", "password": "ValidPass123!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_rejects_int_email(self, client, db_session):
        """Test /register rejects non-string email via API."""
        resp = await client.post(
            "/api/v1/users/register",
            json={"email": 12345, "password": "ValidPass123!"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_rejects_invalid_email(self, client, db_session):
        """Test /login rejects invalid email format via API."""
        resp = await client.post(
            "/api/v1/users/login",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_rejects_long_name(self, client, db_session):
        """Test /register rejects names over 200 chars."""
        resp = await client.post(
            "/api/v1/users/register",
            json={
                "email": "valid@example.com",
                "password": "ValidPass123!",
                "full_name": "A" * 201,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_forgot_password_rejects_invalid_email(self, client, db_session):
        """Test /forgot-password rejects invalid email."""
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert resp.status_code == 422


# ============================================================
# 6. Security Headers Tests
# ============================================================

class TestSecurityHeaders:
    """Test security headers are properly set on responses."""

    @pytest.mark.asyncio
    async def test_x_frame_options_deny(self, client):
        """Responses include X-Frame-Options: DENY."""
        response = await client.get("/")
        assert response.headers.get("X-Frame-Options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, client, db_session):
        """Test X-Frame-Options header is DENY."""
        resp = await client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_content_type_options_nosniff(self, client):
        """Responses include X-Content-Type-Options: nosniff."""
        response = await client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, client, db_session):
        """Test X-Content-Type-Options header is nosniff."""
        resp = await client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_strict_transport_security(self, client):
        """Responses include Strict-Transport-Security header."""
        response = await client.get("/")
        hsts = response.headers.get("Strict-Transport-Security", "")
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    @pytest.mark.asyncio
    async def test_hsts_header(self, client, db_session):
        """Test Strict-Transport-Security header is set."""
        resp = await client.get("/health")
        hsts = resp.headers.get("strict-transport-security", "")
        assert "max-age=" in hsts

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client):
        """Responses include Referrer-Policy header."""
        response = await client.get("/")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_referrer_policy_db(self, client, db_session):
        """Test Referrer-Policy header is set."""
        resp = await client.get("/health")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_x_xss_protection(self, client):
        """Responses include X-XSS-Protection header."""
        response = await client.get("/")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_xss_protection(self, client, db_session):
        """Test X-XSS-Protection header is set."""
        resp = await client.get("/health")
        assert resp.headers.get("x-xss-protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_permissions_policy(self, client):
        """Responses include Permissions-Policy header."""
        response = await client.get("/")
        permissions = response.headers.get("Permissions-Policy", "")
        assert "geolocation=()" in permissions

    @pytest.mark.asyncio
    async def test_health_endpoint_has_security_headers(self, client):
        """Even health endpoint responses include security headers."""
        response = await client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
