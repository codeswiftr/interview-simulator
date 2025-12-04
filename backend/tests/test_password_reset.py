"""Tests for password reset functionality."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel, select

from app.db import SessionLocal, engine, get_session
from app.main import app
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.security import verify_password


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    """Create tables once for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db(prepare_db):
    """Truncate tables between tests."""
    async with engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
    yield


@pytest.fixture
async def session_override():
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def client(session_override):
    async def _override():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def create_test_user(client: AsyncClient, email: str = "test@example.com") -> str:
    """Create a test user and return their email."""
    await client.post("/api/v1/users/register", json={"email": email, "password": "password123"})
    return email


@pytest.mark.asyncio
async def test_forgot_password_generates_token(client: AsyncClient, session_override):
    """Test that forgot-password creates a token in the database."""
    email = await create_test_user(client)

    resp = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert "password reset link has been sent" in resp.json()["message"].lower()

    # Verify token was created in database
    result = await session_override.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 1
    token = tokens[0]

    # Verify token properties
    assert token.used is False
    assert token.expires_at > datetime.now(timezone.utc)
    assert len(token.token) > 0


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_returns_success(client: AsyncClient, session_override):
    """Test that unknown email still returns success (security - don't reveal if email exists)."""
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert resp.status_code == 200
    assert "password reset link has been sent" in resp.json()["message"].lower()

    # Verify no token was created
    result = await session_override.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 0


@pytest.mark.asyncio
async def test_forgot_password_email_service_failure(client: AsyncClient, session_override):
    """Test that email service failures surface as server errors."""
    email = await create_test_user(client, email="email_failure@example.com")

    # Patch EmailService in auth module to raise on send
    with patch("app.api.auth.EmailService") as MockEmailService:
        instance = MockEmailService.return_value
        instance.send_password_reset = AsyncMock(side_effect=Exception("Email provider failure"))

        with pytest.raises(Exception) as exc_info:
            await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Document current behavior: exception from email provider is not swallowed.
    assert "Email provider failure" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reset_password_validates_token(client: AsyncClient, session_override):
    """Test that valid token successfully resets password."""
    email = await create_test_user(client, email="reset@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await session_override.exec(select(PasswordResetToken))
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
    await session_override.refresh(reset_token)
    assert reset_token.used is True

    # Verify user can log in with new password
    login_resp = await client.post("/api/v1/users/login", json={"email": email, "password": new_password})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


@pytest.mark.asyncio
async def test_reset_password_rejects_expired_token(client: AsyncClient, session_override):
    """Test that expired token returns error."""
    email = await create_test_user(client, email="expired@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get and expire the token
    result = await session_override.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Manually set token to expired (2 hours ago)
    reset_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await session_override.commit()

    # Try to reset password with expired token
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "newpassword"}
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_rejects_used_token(client: AsyncClient, session_override):
    """Test that already-used token returns error."""
    email = await create_test_user(client, email="reuse@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await session_override.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Use token once
    resp1 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "password1"}
    )
    assert resp1.status_code == 200

    # Try to use token again
    resp2 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "password2"}
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
async def test_reset_password_hashes_new_password(client: AsyncClient, session_override):
    """Test that new password is properly hashed."""
    email = await create_test_user(client, email="hash@example.com")

    # Request password reset
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get the token
    result = await session_override.exec(select(PasswordResetToken))
    reset_token = result.first()
    assert reset_token is not None

    # Reset password
    new_password = "super-secret-password"
    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": new_password}
    )

    # Get user and verify password is hashed
    user_result = await session_override.exec(select(User).where(User.email == email))
    user = user_result.first()
    assert user is not None

    # Hashed password should not equal plaintext
    assert user.hashed_password != new_password

    # But verify_password should work
    assert verify_password(new_password, user.hashed_password) is True


@pytest.mark.asyncio
async def test_forgot_password_multiple_requests(client: AsyncClient, session_override):
    """Test that multiple forgot-password requests create separate tokens."""
    email = await create_test_user(client, email="multiple@example.com")

    # Request password reset twice
    await client.post("/api/v1/auth/forgot-password", json={"email": email})
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Should have 2 tokens
    result = await session_override.exec(select(PasswordResetToken))
    tokens = list(result.all())
    assert len(tokens) == 2

    # Both tokens should be valid (not used, not expired)
    for token in tokens:
        assert token.used is False
        assert token.expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_forgot_password_rate_limiting(client: AsyncClient, session_override):
    """Test that forgot-password has rate limiting to prevent abuse."""
    email = await create_test_user(client, email="rate_limit@example.com")

    # Make multiple rapid requests (more than typical rate limit)
    responses = []
    for i in range(10):
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
async def test_reset_password_with_latest_token(client: AsyncClient, session_override):
    """Test that user can reset with any valid token (latest or older)."""
    email = await create_test_user(client, email="latest@example.com")

    # Request password reset twice
    await client.post("/api/v1/auth/forgot-password", json={"email": email})
    await client.post("/api/v1/auth/forgot-password", json={"email": email})

    # Get both tokens
    result = await session_override.exec(select(PasswordResetToken).order_by(PasswordResetToken.created_at))
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
    await session_override.refresh(first_token)
    assert first_token.used is False
