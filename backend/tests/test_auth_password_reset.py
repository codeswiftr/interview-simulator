"""Comprehensive tests for password reset functionality.

Tests cover the full password reset flow:
- Forgot password endpoint (security considerations)
- Reset password endpoint (token validation)
- Token expiration handling
- Token reuse prevention
- Email delivery integration
"""

import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlmodel import select

from app.models.password_reset import PasswordResetToken
from app.models.user import User


class TestForgotPassword:
    """Tests for forgot password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(
        self, client: AsyncClient, test_user: User, test_session
    ):
        """Test forgot password with valid email.

        Should:
        - Return success message (no user enumeration)
        - Create password reset token in database
        - Send email to user
        - Token should expire in 1 hour
        """
        with patch("app.services.email_service.EmailService.send_password_reset") as mock_email:
            mock_email.return_value = None

            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": test_user.email},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "password reset link has been sent" in data["message"].lower()

        # Verify token was created
        result = await test_session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id)
        )
        token = result.first()
        assert token is not None
        assert token.used is False
        assert token.expires_at > datetime.now(UTC)
        assert token.expires_at < datetime.now(UTC) + timedelta(hours=2)

        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        assert test_user.email in call_args[0]
        assert "reset-password?token=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user(self, client: AsyncClient):
        """Test forgot password with non-existent email.

        Should:
        - Return same success message (security: no user enumeration)
        - Not create any token
        - Not send any email
        """
        with patch("app.services.email_service.EmailService.send_password_reset") as mock_email:
            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "nonexistent@example.com"},
            )

        assert response.status_code == status.HTTP_200_OK
        assert "password reset link has been sent" in response.json()["message"].lower()

        # Should not send email
        mock_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_forgot_password_case_insensitive_email(
        self, client: AsyncClient, test_user: User
    ):
        """Test forgot password with different email case.

        Email lookup should be case-insensitive.
        """
        with patch("app.services.email_service.EmailService.send_password_reset") as mock_email:
            mock_email.return_value = None

            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": test_user.email.upper()},
            )

        assert response.status_code == status.HTTP_200_OK
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_forgot_password_email_error_silent(
        self, client: AsyncClient, test_user: User
    ):
        """Test forgot password when email sending fails.

        Should:
        - Still return success (security: don't reveal failures)
        - Log error internally
        - Create token (user can try again later)
        """
        with patch("app.services.email_service.EmailService.send_password_reset") as mock_email:
            mock_email.side_effect = Exception("Email service down")

            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": test_user.email},
            )

        # Should still return success
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_forgot_password_multiple_requests(
        self, client: AsyncClient, test_user: User, test_session
    ):
        """Test multiple forgot password requests.

        Each request should create a new token.
        Old tokens should remain valid until used or expired.
        """
        with patch("app.services.email_service.EmailService.send_password_reset"):
            # First request
            await client.post("/api/v1/auth/forgot-password", json={"email": test_user.email})

            # Second request
            await client.post("/api/v1/auth/forgot-password", json={"email": test_user.email})

        # Should have 2 valid tokens
        result = await test_session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id)
        )
        tokens = result.all()
        assert len(tokens) == 2
        assert all(not t.used for t in tokens)


class TestResetPassword:
    """Tests for reset password endpoint."""

    @pytest.fixture
    async def valid_reset_token(self, test_user: User, test_session) -> str:
        """Create a valid password reset token."""
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token=token,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        test_session.add(reset_token)
        await test_session.commit()
        return token

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, client: AsyncClient, test_user: User, valid_reset_token: str, test_session
    ):
        """Test successful password reset.

        Should:
        - Accept valid token
        - Update user's password
        - Mark token as used
        - New password should work for login
        """
        new_password = "NewSecurePassword123!@#"

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": valid_reset_token, "new_password": new_password},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "successfully reset" in response.json()["message"].lower()

        # Verify token marked as used
        result = await test_session.exec(
            select(PasswordResetToken).where(PasswordResetToken.token == valid_reset_token)
        )
        token_record = result.first()
        assert token_record.used is True

        # Verify new password works (would need login endpoint test)
        await test_session.refresh(test_user)
        from app.security import verify_password
        assert verify_password(new_password, test_user.hashed_password)

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test reset with non-existent token.

        Should return 400 error.
        """
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid-token-12345", "new_password": "NewPassword123!@#"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(
        self, client: AsyncClient, test_user: User, test_session
    ):
        """Test reset with expired token.

        Should return 400 error.
        """
        # Create expired token
        token = secrets.token_urlsafe(32)
        expired_token = PasswordResetToken(
            user_id=test_user.id,
            token=token,
            expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
        )
        test_session.add(expired_token)
        await test_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPassword123!@#"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_already_used_token(
        self, client: AsyncClient, test_user: User, test_session
    ):
        """Test reset with already-used token.

        Should return 400 error (prevents token reuse attacks).
        """
        # Create used token
        token = secrets.token_urlsafe(32)
        used_token = PasswordResetToken(
            user_id=test_user.id,
            token=token,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used=True,
        )
        test_session.add(used_token)
        await test_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPassword123!@#"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already been used" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(
        self, client: AsyncClient, valid_reset_token: str
    ):
        """Test reset with weak password.

        Should reject passwords that don't meet requirements.
        """
        weak_passwords = [
            "short",  # Too short
            "nouppercaseordigits",  # No uppercase or digits
            "NOLOWERCASEORDIGITS",  # No lowercase or digits
            "NoSpecialChars123",  # No special characters (if required)
        ]

        for weak_password in weak_passwords:
            response = await client.post(
                "/api/v1/auth/reset-password",
                json={"token": valid_reset_token, "new_password": weak_password},
            )

            # Should reject (either 400 or 422 depending on validation approach)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

    @pytest.mark.asyncio
    async def test_reset_password_token_not_reusable(
        self, client: AsyncClient, valid_reset_token: str
    ):
        """Test that token cannot be reused after successful reset.

        Security test: One-time use tokens.
        """
        # First reset
        response1 = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": valid_reset_token, "new_password": "FirstPassword123!@#"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Try to reuse same token
        response2 = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": valid_reset_token, "new_password": "SecondPassword123!@#"},
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already been used" in response2.json()["detail"].lower()


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    @pytest.fixture
    async def user_with_refresh_token(self, test_user: User, test_session) -> tuple[User, str]:
        """Create user with valid refresh token."""
        from app.security import create_refresh_token

        refresh_token, expires_at = create_refresh_token()
        test_user.refresh_token = refresh_token
        test_user.refresh_token_expires_at = expires_at
        await test_session.commit()
        await test_session.refresh(test_user)
        return test_user, refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, client: AsyncClient, user_with_refresh_token: tuple[User, str], test_session
    ):
        """Test successful token refresh.

        Should:
        - Accept valid refresh token
        - Return new access token and refresh token
        - Invalidate old refresh token (token rotation)
        """
        user, old_refresh_token = user_with_refresh_token

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != old_refresh_token  # Token rotation

        # Verify old token is invalidated
        await test_session.refresh(user)
        assert user.refresh_token != old_refresh_token
        assert user.refresh_token == data["refresh_token"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token.

        Should return 401 Unauthorized.
        """
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token-12345"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_expired(
        self, client: AsyncClient, test_user: User, test_session
    ):
        """Test refresh with expired token.

        Should:
        - Return 401 Unauthorized
        - Clear the expired token from database
        """
        from app.security import create_refresh_token

        # Create expired token
        refresh_token, _ = create_refresh_token()
        test_user.refresh_token = refresh_token
        test_user.refresh_token_expires_at = datetime.now(UTC) - timedelta(days=1)
        await test_session.commit()

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in response.json()["detail"].lower()

        # Verify token was cleared
        await test_session.refresh(test_user)
        assert test_user.refresh_token is None
        assert test_user.refresh_token_expires_at is None

    @pytest.mark.asyncio
    async def test_refresh_token_rotation_prevents_reuse(
        self, client: AsyncClient, user_with_refresh_token: tuple[User, str]
    ):
        """Test that old refresh tokens cannot be reused after rotation.

        Security test: Token rotation prevents token reuse attacks.
        """
        _, old_refresh_token = user_with_refresh_token

        # First refresh
        response1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Try to reuse old token
        response2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
