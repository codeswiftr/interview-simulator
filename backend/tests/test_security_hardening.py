"""Security hardening tests for Sprint 9 P0.

Tests:
- Input validation (Pydantic strict mode, EmailStr)
- Per-endpoint auth rate limiting
- CORS configuration
- Security headers
"""

import pytest
from pydantic import ValidationError


class TestInputValidation:
    """Test Pydantic strict mode and input validation."""

    def test_user_create_rejects_invalid_email(self):
        """Test UserCreate rejects malformed emails."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError) as exc:
            UserCreate(email="not-an-email", password="ValidPass123!")
        assert "email" in str(exc.value).lower()

    def test_user_create_rejects_email_without_domain(self):
        """Test UserCreate rejects emails without domain."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(email="user@", password="ValidPass123!")

    def test_user_create_accepts_valid_email(self):
        """Test UserCreate accepts properly formatted emails."""
        from app.models.user import UserCreate

        user = UserCreate(email="valid@example.com", password="ValidPass123!")
        assert user.email == "valid@example.com"

    def test_user_create_rejects_int_email(self):
        """Test strict mode rejects non-string email."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(email=12345, password="ValidPass123!")

    def test_user_create_rejects_int_password(self):
        """Test strict mode rejects non-string password."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(email="valid@example.com", password=12345)

    def test_user_create_full_name_max_length(self):
        """Test UserCreate enforces full_name max_length=200."""
        from app.models.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(
                email="valid@example.com",
                password="ValidPass123!",
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

    def test_user_login_rejects_invalid_email(self):
        """Test UserLogin rejects malformed emails."""
        from app.models.user import UserLogin

        with pytest.raises(ValidationError):
            UserLogin(email="not-an-email", password="password")

    def test_user_login_strict_mode(self):
        """Test UserLogin strict mode rejects non-string types."""
        from app.models.user import UserLogin

        with pytest.raises(ValidationError):
            UserLogin(email=123, password="password")

    def test_user_update_rejects_invalid_email(self):
        """Test UserUpdate rejects malformed emails."""
        from app.models.user import UserUpdate

        with pytest.raises(ValidationError):
            UserUpdate(email="invalid-email")

    def test_user_update_accepts_none_email(self):
        """Test UserUpdate accepts None email (optional field)."""
        from app.models.user import UserUpdate

        update = UserUpdate(full_name="Test Name")
        assert update.email is None

    def test_user_update_full_name_max_length(self):
        """Test UserUpdate enforces full_name max_length=200."""
        from app.models.user import UserUpdate

        with pytest.raises(ValidationError):
            UserUpdate(full_name="A" * 201)

    def test_password_change_strict_mode(self):
        """Test PasswordChange strict mode rejects non-string types."""
        from app.models.user import PasswordChange

        with pytest.raises(ValidationError):
            PasswordChange(current_password=123, new_password="ValidPass123!")

    def test_refresh_token_strict_mode(self):
        """Test RefreshTokenRequest strict mode rejects non-string types."""
        from app.models.user import RefreshTokenRequest

        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token=12345)

    def test_forgot_password_rejects_invalid_email(self):
        """Test ForgotPasswordRequest rejects malformed emails."""
        from app.api.auth import ForgotPasswordRequest

        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email="not-an-email")

    def test_forgot_password_strict_mode(self):
        """Test ForgotPasswordRequest strict mode rejects non-string types."""
        from app.api.auth import ForgotPasswordRequest

        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email=12345)

    def test_reset_password_token_max_length(self):
        """Test ResetPasswordRequest token max_length=200."""
        from app.api.auth import ResetPasswordRequest

        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                token="A" * 201,
                new_password="ValidPass123!",
            )

    def test_reset_password_password_max_length(self):
        """Test ResetPasswordRequest new_password max_length=200."""
        from app.api.auth import ResetPasswordRequest

        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                token="valid-token",
                new_password="A" * 201,
            )


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


class TestSecurityHeaders:
    """Test security headers are present."""

    @pytest.mark.asyncio
    async def test_x_frame_options(self, client, db_session):
        """Test X-Frame-Options header is DENY."""
        resp = await client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, client, db_session):
        """Test X-Content-Type-Options header is nosniff."""
        resp = await client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client, db_session):
        """Test Referrer-Policy header is set."""
        resp = await client.get("/health")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_hsts_header(self, client, db_session):
        """Test Strict-Transport-Security header is set."""
        resp = await client.get("/health")
        hsts = resp.headers.get("strict-transport-security", "")
        assert "max-age=" in hsts

    @pytest.mark.asyncio
    async def test_xss_protection(self, client, db_session):
        """Test X-XSS-Protection header is set."""
        resp = await client.get("/health")
        assert resp.headers.get("x-xss-protection") == "1; mode=block"


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
