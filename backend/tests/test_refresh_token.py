"""Tests for JWT refresh token migration.

Validates that refresh tokens are now issued as forge-shared JWTs
(not opaque strings) and that verification checks JWT signature + type.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.security import (
    create_refresh_token,
    decode_token,
    get_jwt_auth_instance,
    verify_refresh_token,
)


class TestJWTRefreshTokenCreation:
    """Test that refresh tokens are proper JWTs."""

    def test_refresh_token_is_jwt(self):
        """Refresh token should be a JWT with three dot-separated segments."""
        token, _ = create_refresh_token("user-123")
        parts = token.split(".")
        assert len(parts) == 3, "Refresh token should be a JWT (header.payload.signature)"

    def test_refresh_token_has_refresh_type(self):
        """Refresh token JWT payload should have type='refresh'."""
        token, _ = create_refresh_token("user-123")
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.type == "refresh"

    def test_refresh_token_contains_user_id(self):
        """Refresh token should embed the user_id as 'sub' claim."""
        token, _ = create_refresh_token("user-456")
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.sub == "user-456"

    def test_refresh_token_expiry_is_future(self):
        """Expiry returned should be ~7 days in the future."""
        _, expires_at = create_refresh_token("user-123")
        now = datetime.now(UTC)
        assert expires_at > now
        assert expires_at < now + timedelta(days=8)

    def test_refresh_tokens_differ_by_user(self):
        """Refresh tokens for different users should differ."""
        t1, _ = create_refresh_token("user-123")
        t2, _ = create_refresh_token("user-456")
        assert t1 != t2


class TestJWTRefreshTokenVerification:
    """Test verify_refresh_token with JWT-based tokens."""

    def test_valid_token_passes(self):
        """A freshly created token should verify successfully."""
        token, expires_at = create_refresh_token("user-123")
        assert verify_refresh_token(token, token, expires_at) is True

    def test_mismatched_stored_token_fails(self):
        """Providing a different token than stored should fail."""
        token, expires_at = create_refresh_token("user-123")
        other_token, _ = create_refresh_token("user-456")
        assert verify_refresh_token(token, other_token, expires_at) is False

    def test_expired_db_timestamp_fails(self):
        """Token with expired DB timestamp should be rejected."""
        token, _ = create_refresh_token("user-123")
        expired = datetime.now(UTC) - timedelta(days=1)
        assert verify_refresh_token(token, token, expired) is False

    def test_none_stored_token_fails(self):
        """None stored token should be rejected."""
        assert verify_refresh_token(None, "some-token", datetime.now(UTC) + timedelta(days=1)) is False

    def test_none_expires_at_fails(self):
        """None expiry should be rejected."""
        token, _ = create_refresh_token("user-123")
        assert verify_refresh_token(token, token, None) is False

    def test_non_jwt_token_fails_verification(self):
        """An opaque string should fail JWT signature check."""
        opaque = "not-a-jwt-token-just-random-string"
        future = datetime.now(UTC) + timedelta(days=7)
        assert verify_refresh_token(opaque, opaque, future) is False

    def test_access_token_fails_as_refresh(self):
        """An access token should fail refresh verification (wrong type)."""
        from app.security import create_access_token

        access = create_access_token({"sub": "user-123"})
        future = datetime.now(UTC) + timedelta(days=7)
        # access token has type="access", not "refresh"
        assert verify_refresh_token(access, access, future) is False


class TestTokenRotation:
    """Test that token rotation produces valid new tokens."""

    def test_rotated_tokens_are_valid(self):
        """Both old and new rotation tokens should be valid JWTs."""
        old_token, old_exp = create_refresh_token("user-123")
        new_token, new_exp = create_refresh_token("user-123")
        # Both should verify independently
        assert verify_refresh_token(old_token, old_token, old_exp) is True
        assert verify_refresh_token(new_token, new_token, new_exp) is True

    def test_rotated_token_is_valid_jwt(self):
        """New refresh token should also be a valid JWT."""
        token, expires_at = create_refresh_token("user-123")
        assert verify_refresh_token(token, token, expires_at) is True
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.type == "refresh"
        assert payload.sub == "user-123"
