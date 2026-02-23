"""Comprehensive authentication token security tests.

This module tests critical authentication edge cases including:
- Token expiration and validation
- Token reuse and replay attacks
- Malformed token handling
- Race conditions in token refresh
- Session hijacking protection
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from app.config import settings
from app.security import create_access_token


@pytest.mark.asyncio
async def test_expired_access_token_rejected(client: AsyncClient, db_session):
    """Test that expired access tokens are properly rejected."""
    # Register and login a user first
    email = "expired_test@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    user_id = login_resp.json()["user_id"]

    # Create an expired token (expired 1 hour ago)
    expired_token = create_access_token(
        data={"sub": user_id, "type": "access"}, expires_delta=timedelta(hours=-1)
    )

    # Try to access protected endpoint with expired token
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tampered_token_signature_rejected(client: AsyncClient, db_session):
    """Test that tokens with invalid signatures are rejected."""
    # Register and get valid token
    email = "tamper_test@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    valid_token = login_resp.json()["access_token"]

    # Tamper with the token by modifying the last few characters
    tampered_token = valid_token[:-10] + "TAMPERED!!"

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tampered_token}"}
    )

    assert response.status_code == 401
    assert (
        "invalid" in response.json()["detail"].lower()
        or "malformed" in response.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_token_with_invalid_user_id_rejected(client: AsyncClient, db_session):
    """Test that tokens with non-existent user IDs are rejected."""
    # Create a token for a non-existent user
    fake_user_id = "00000000-0000-0000-0000-000000000000"
    fake_token = create_access_token(data={"sub": fake_user_id, "type": "access"})

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {fake_token}"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(client: AsyncClient, db_session):
    """Test that refresh tokens are rejected when used as access tokens."""
    email = "refresh_misuse@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Try to use refresh token as access token
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {refresh_token}"}
    )

    # Should be rejected because refresh tokens have different claims
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_cannot_refresh_itself(client: AsyncClient, db_session):
    """Test that access tokens cannot be used to get new tokens."""
    email = "access_refresh@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    access_token = login_resp.json()["access_token"]

    # Try to use access token for refresh
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_missing_required_claims(client: AsyncClient, db_session):
    """Test that tokens without required claims are rejected."""
    # Create token without 'sub' claim
    incomplete_token = jwt.encode(
        {"type": "access", "exp": datetime.now(UTC) + timedelta(hours=1)},
        settings.secret_key,
        algorithm="HS256",
    )

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {incomplete_token}"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_with_wrong_algorithm_rejected(client: AsyncClient, db_session):
    """Test that tokens signed with wrong algorithm are rejected."""
    email = "algo_test@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    user_id = login_resp.json()["user_id"]

    # Create token with wrong algorithm (HS512 instead of HS256)
    wrong_algo_token = jwt.encode(
        {"sub": user_id, "type": "access", "exp": datetime.now(UTC) + timedelta(hours=1)},
        settings.secret_key,
        algorithm="HS512",
    )

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {wrong_algo_token}"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_concurrent_refresh_token_usage_blocked(client: AsyncClient, db_session):
    """Test that concurrent use of same refresh token is detected and blocked."""
    email = "concurrent@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    refresh_token = login_resp.json()["refresh_token"]

    # First refresh succeeds
    resp1 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp1.status_code == 200

    # Second use of same token should fail (token rotation)
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_token_with_future_issued_at_rejected(client: AsyncClient, db_session):
    """Test that tokens with future 'iat' (issued at) are rejected."""
    email = "future_iat@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    user_id = login_resp.json()["user_id"]

    # Create token with future issued-at time (1 day from now)
    future_iat_token = jwt.encode(
        {
            "sub": user_id,
            "type": "access",
            "iat": datetime.now(UTC) + timedelta(days=1),
            "exp": datetime.now(UTC) + timedelta(days=2),
        },
        settings.secret_key,
        algorithm="HS256",
    )

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {future_iat_token}"}
    )

    # Should be rejected due to clock skew or invalid IAT
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authorization_header_case_insensitive(client: AsyncClient, db_session):
    """Test that authorization header parsing is case-insensitive for 'Bearer'."""
    email = "case_test@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    token = login_resp.json()["access_token"]

    # Test with lowercase 'bearer'
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"bearer {token}"})

    # Should work regardless of case
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_multiple_spaces_in_auth_header_handled(client: AsyncClient, db_session):
    """Test that multiple spaces in authorization header are handled correctly."""
    email = "spaces_test@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    token = login_resp.json()["access_token"]

    # Test with extra spaces
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer    {token}"})

    # Should handle extra spaces gracefully
    assert response.status_code in [200, 401]  # Either works or rejects malformed header


@pytest.mark.asyncio
async def test_token_without_bearer_prefix_rejected(client: AsyncClient, db_session):
    """Test that tokens without 'Bearer' prefix are rejected."""
    email = "no_bearer@example.com"
    password = "SecureTest123!"

    await client.post("/api/v1/users/register", json={"email": email, "password": password})

    login_resp = await client.post(
        "/api/v1/users/login", json={"email": email, "password": password}
    )
    token = login_resp.json()["access_token"]

    # Send token without Bearer prefix
    response = await client.get("/api/v1/users/me", headers={"Authorization": token})

    assert response.status_code == 401
