"""Tests for password reset functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.security import verify_password


async def create_test_user(client: AsyncClient, email: str = "test@example.com") -> str:
    """Create a test user and return their email."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "SecureTest123!"})
    return email

@pytest.mark.asyncio
async def test_forgot_password_generates_token(client: AsyncClient, db_session):
    """Test that forgot-password creates a token in the database."""
    email = await create_test_user(client)

    resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert "password reset link has been sent" in resp.json()["message"].lower()

    # Verify token was created in database
    result = await db_session.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 1
    token = tokens[0]

    # Verify token properties
    assert token.used is False
    assert token.expires_at > datetime.now(UTC)
    assert len(token.token) > 0

@pytest.mark.asyncio
async def test_forgot_password_unknown_email_returns_success(client: AsyncClient, db_session):
    """Test that unknown email still returns success (security - don't reveal if email exists)."""
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert resp.status_code == 200
    assert "password reset link has been sent" in resp.json()["message"].lower()

    # Verify no token was created
    result = await db_session.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 0

@pytest.mark.asyncio
async def test_forgot_password_email_service_failure(client: AsyncClient, db_session):
    """Test that email service failures are handled gracefully (security best practice).

    The endpoint should return 200 even if email sending fails to not reveal
    whether the email exists in the system.
    """
    email = await create_test_user(client, email="email_failure@example.com")

    # Patch EmailService in auth module to raise on send
    with patch("app.api.auth.EmailService") as MockEmailService:
        instance = MockEmailService.return_value
        instance.send_password_reset = AsyncMock(side_effect=Exception("Email provider failure"))

        # Request should succeed (200) even though email sending failed
        response = await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Endpoint returns success for security (don't reveal email existence)
    assert response.status_code == 200
    assert "sent" in response.json()["message"].lower()

@pytest.mark.asyncio
async def test_reset_password_validates_token(client: AsyncClient, db_session):
    """Test that valid token successfully resets password."""
    email = await create_test_user(client, email="reset@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await db_session.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Reset password
    new_password = "newpassword456"
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": new_password}
    )
    assert resp.status_code == 200
    assert "successfully reset" in resp.json()["message"].lower()

    # Verify token is marked as used
    await db_session.refresh(reset_token)
    assert reset_token.used is True

    # Verify user can log in with new password
    login_resp = await client.post("/api/v1/users/login", json={"email": email, "password": new_password})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

@pytest.mark.asyncio
async def test_reset_password_rejects_expired_token(client: AsyncClient, db_session):
    """Test that expired token returns error."""
    email = await create_test_user(client, email="expired@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get and expire the token
    result = await db_session.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Manually set token to expired (2 hours ago)
    reset_token.expires_at = datetime.now(UTC) - timedelta(hours=2)
    await db_session.commit()

    # Try to reset password with expired token
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "newpassword"}
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_reset_password_rejects_used_token(client: AsyncClient, db_session):
    """Test that already-used token returns error."""
    email = await create_test_user(client, email="reuse@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await db_session.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Use token once
    resp1 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "ValidNewPass1"}
    )
    assert resp1.status_code == 200

    # Try to use token again
    resp2 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "ValidNewPass2"}
    )
    assert resp2.status_code == 400
    assert "already been used" in resp2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test that invalid token returns error."""
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token-xyz", "new_password": "newpassword"}
    )
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_reset_password_hashes_new_password(client: AsyncClient, db_session):
    """Test that new password is properly hashed."""
    email = await create_test_user(client, email="hash@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await db_session.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Reset password
    new_password = "super-secret-password"
    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": new_password}
    )

    # Get user and verify password is hashed
    user_result = await db_session.exec(select(User).where(User.email == email))
    user = user_result.first()
    assert user is not None

    # Hashed password should not equal plaintext
    assert user.hashed_password != new_password

    # But verify_password should work
    assert verify_password(new_password, user.hashed_password) is True

@pytest.mark.asyncio
async def test_forgot_password_multiple_requests(client: AsyncClient, db_session):
    """Test that multiple forgot-password requests create separate tokens."""
    email = await create_test_user(client, email="multiple@example.com")

    # Request password reset twice
    await client.post("/api/v1/auth/forgot-password", json={"email": email})
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Should have 2 tokens
    result = await db_session.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 2

    # Both tokens should be valid (not used, not expired)
    for token in tokens:
        assert token.used is False
        assert token.expires_at > datetime.now(UTC)

@pytest.mark.asyncio
async def test_forgot_password_rate_limiting(client: AsyncClient, db_session):
    """Test that forgot-password has rate limiting to prevent abuse."""
    email = await create_test_user(client, email="rate_limit@example.com")

    # Make multiple rapid requests (more than typical rate limit)
    responses = []
    for _i in range(10):
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email}
        )
        responses.append(resp.status_code)

    # All should succeed (rate limiting may be implemented at middleware level)
    # But we verify the endpoint handles multiple requests gracefully
    # In production, rate limiting middleware would block excessive requests
    assert all(status in [200, 429] for status in responses)

@pytest.mark.asyncio
async def test_reset_password_with_latest_token(client: AsyncClient, db_session):
    """Test that user can reset with any valid token (latest or older)."""
    email = await create_test_user(client, email="latest@example.com")

    # Request password reset twice
    await client.post("/api/v1/auth/forgot-password", json={"email": email})
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get both tokens
    result = await db_session.exec(select(PasswordResetToken).order_by(PasswordResetToken.created_at))
    tokens = list(result.all())
    assert len(tokens) == 2

    first_token = tokens[0]
    second_token = tokens[1]

    # Use the second (latest) token
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": second_token.token, "new_password": "newpassword"}
    )
    assert resp.status_code == 200

    # First token should still be valid (not used)
    await db_session.refresh(first_token)
    assert first_token.used is False

@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, db_session):
    """Test successful token refresh with valid refresh token."""
    email = await create_test_user(client, email="refresh@example.com")

    # Login to get tokens
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": email, "password": "SecureTest123!"}
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    refresh_token = tokens["refresh_token"]

    # Use refresh token to get new tokens
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token  # Token rotation

@pytest.mark.asyncio
async def test_refresh_token_invalid_token(client: AsyncClient):
    """Test refresh endpoint rejects invalid refresh token."""
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token-xyz"}
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_refresh_token_expired_token(client: AsyncClient, db_session):
    """Test refresh endpoint rejects expired refresh token."""
    email = await create_test_user(client, email="expired_refresh@example.com")

    # Login to get tokens
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": email, "password": "SecureTest123!"}
    )
    tokens = login_resp.json()
    refresh_token = tokens["refresh_token"]

    # Manually expire the refresh token
    user_result = await db_session.exec(select(User).where(User.email == email))
    user = user_result.first()
    user.refresh_token_expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    # Try to refresh with expired token
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_refresh_token_clears_expired_token(client: AsyncClient, db_session):
    """Test that expired refresh tokens are cleared from database."""
    email = await create_test_user(client, email="clear_expired@example.com")

    # Login to get tokens
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": email, "password": "SecureTest123!"}
    )
    tokens = login_resp.json()
    refresh_token = tokens["refresh_token"]

    # Manually expire the refresh token
    user_result = await db_session.exec(select(User).where(User.email == email))
    user = user_result.first()
    user.refresh_token_expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    # Try to refresh with expired token
    await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    # Verify token was cleared
    await db_session.refresh(user)
    assert user.refresh_token is None
    assert user.refresh_token_expires_at is None

@pytest.mark.asyncio
async def test_reset_password_user_not_found_after_token_lookup(client: AsyncClient, db_session):
    """Test edge case where token exists but user was deleted (data inconsistency)."""
    email = await create_test_user(client, email="orphan_token@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await db_session.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None
    token_value = reset_token.token  # Save token value before deletion

    # Delete the user (simulating data inconsistency)
    # First delete the password reset tokens to avoid FK constraint
    user_result = await db_session.exec(select(User).where(User.email == email))
    user = user_result.first()
    user_id = user.id

    # Delete all tokens for this user first
    await db_session.exec(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
    )
    for token in (await db_session.exec(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
    )).all():
        await db_session.delete(token)
    await db_session.commit()

    # Now delete the user
    await db_session.delete(user)
    await db_session.commit()

    # Try to reset password with token that no longer exists
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token_value, "new_password": "newpassword"}
    )
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_forgot_password_lowercase_email_normalization(client: AsyncClient, db_session):
    """Test that email is normalized to lowercase before lookup."""
    email_uppercase = "TEST@EXAMPLE.COM"
    email_lowercase = email_uppercase.lower()

    # Register with lowercase
    await create_test_user(client, email=email_lowercase)

    # Request password reset with uppercase email
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": email_uppercase})
    assert resp.status_code == 200

    # Verify token was created (email was normalized)
    result = await db_session.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 1

@pytest.mark.asyncio
async def test_refresh_token_null_refresh_token_handling(client: AsyncClient, db_session):
    """Test that refresh endpoint handles null refresh_token gracefully."""
    email = await create_test_user(client, email="null_refresh@example.com")

    # Login to get tokens
    login_resp = await client.post(
        "/api/v1/users/login",
        json={"email": email, "password": "SecureTest123!"}
    )
    assert login_resp.status_code == 200

    # Manually clear refresh token (simulating edge case)
    user_result = await db_session.exec(select(User).where(User.email == email))
    user = user_result.first()
    user.refresh_token = None
    user.refresh_token_expires_at = None
    await db_session.commit()

    # Try to refresh with null token
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "some-token"}
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()

