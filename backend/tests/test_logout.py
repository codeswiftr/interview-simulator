"""Tests for the POST /api/v1/auth/logout endpoint."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status


class TestLogoutEndpoint:
    """Tests for logout endpoint that invalidates refresh tokens."""

    @pytest.mark.asyncio
    async def test_logout_clears_refresh_token(self, client, auth_headers, test_user):
        """POST /logout should clear the user's refresh token fields."""
        # Set a refresh token on the user first
        test_user.refresh_token = "some_hashed_token"
        test_user.refresh_token_expires_at = datetime.now(UTC) + timedelta(days=7)

        response = await client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert test_user.refresh_token is None
        assert test_user.refresh_token_expires_at is None

    @pytest.mark.asyncio
    async def test_logout_without_auth_returns_401(self, client):
        """POST /logout without auth token should return 401."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token_returns_401(self, client):
        """POST /logout with invalid token should return 401."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout_idempotent(self, client, auth_headers, test_user):
        """Calling logout when no refresh token exists should still succeed."""
        test_user.refresh_token = None
        test_user.refresh_token_expires_at = None

        response = await client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestPasswordResetInvalidatesRefreshToken:
    """Tests that password reset also clears refresh tokens."""

    @pytest.mark.asyncio
    async def test_reset_password_clears_refresh_token(self, client, session, test_user):
        """Password reset should invalidate existing refresh tokens."""
        from app.models.password_reset import PasswordResetToken

        # Set a refresh token
        test_user.refresh_token = "existing_token_hash"
        test_user.refresh_token_expires_at = datetime.now(UTC) + timedelta(days=7)

        # Create a valid reset token
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token="valid_reset_token_123",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        session.add(reset_token)
        await session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "valid_reset_token_123",
                "new_password": "NewSecureP@ss1234!",
            },
        )

        assert response.status_code == 200
        # Refresh token should be cleared
        await session.refresh(test_user)
        assert test_user.refresh_token is None
        assert test_user.refresh_token_expires_at is None
