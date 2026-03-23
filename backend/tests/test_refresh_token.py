"""Tests for JWT refresh token migration.

Validates that refresh tokens are now issued as forge-shared JWTs
(not opaque strings) and that verification checks JWT signature + type.
"""

from datetime import UTC, datetime, timedelta

from app.security import (
    create_refresh_token,
    get_jwt_auth_instance,
    hash_refresh_token,
    verify_refresh_token,
)


class TestJWTRefreshTokenCreation:
    """Test that refresh tokens are proper JWTs."""

    def test_refresh_token_is_jwt(self):
        """Refresh token should be a JWT with three dot-separated segments."""
        token, _ = create_refresh_token("user-123")
        parts = token.split(".")
        assert len(parts) == 3, "Refresh token should be a JWT (header.payload.signature)"

    def test_create_refresh_token_is_jwt_format(self):
        """Test that created refresh tokens are valid JWTs with non-empty parts."""
        user_id = "test-user-123"
        token, _ = create_refresh_token(user_id)

        # JWT tokens have three parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3, "Refresh token should be in JWT format (header.payload.signature)"

        # Each part should be non-empty
        assert all(part for part in parts), "All JWT parts should be non-empty"

    def test_refresh_token_has_refresh_type(self):
        """Refresh token JWT payload should have type='refresh'."""
        token, _ = create_refresh_token("user-123")
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.type == "refresh"

    def test_create_refresh_token_has_refresh_type(self):
        """Test that created tokens have type='refresh'."""
        user_id = "test-user-456"
        token, _ = create_refresh_token(user_id)

        # Decode and verify token type
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.type == "refresh", "Token type should be 'refresh'"

    def test_refresh_token_contains_user_id(self):
        """Refresh token should embed the user_id as 'sub' claim."""
        token, _ = create_refresh_token("user-456")
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.sub == "user-456"

    def test_create_refresh_token_contains_user_id(self):
        """Test that refresh token contains the correct user_id."""
        user_id = "test-user-789"
        token, _ = create_refresh_token(user_id)

        # Decode and verify user_id
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.sub == user_id, "Token should contain the correct user_id"

    def test_refresh_token_expiry_is_future(self):
        """Expiry returned should be ~7 days in the future."""
        _, expires_at = create_refresh_token("user-123")
        now = datetime.now(UTC)
        assert expires_at > now
        assert expires_at < now + timedelta(days=8)

    def test_create_refresh_token_expiry_is_future(self):
        """Test that expiry timestamp is in the future."""
        user_id = "test-user-abc"
        token, expires_at = create_refresh_token(user_id)

        now = datetime.now(UTC)
        assert expires_at > now, "Expiry should be in the future"
        assert expires_at <= now + timedelta(days=8), "Expiry should be within 8 days"

    def test_refresh_tokens_differ_by_user(self):
        """Refresh tokens for different users should differ."""
        t1, _ = create_refresh_token("user-123")
        t2, _ = create_refresh_token("user-456")
        assert t1 != t2

    def test_create_refresh_token_different_users_get_different_tokens(self):
        """Test that different users get different tokens."""
        token1, _ = create_refresh_token("user-1")
        token2, _ = create_refresh_token("user-2")

        assert token1 != token2, "Different users should get different tokens"

        # Verify both tokens contain correct user IDs
        auth = get_jwt_auth_instance()
        payload1 = auth.decode_token(token1)
        payload2 = auth.decode_token(token2)

        assert payload1.sub == "user-1"
        assert payload2.sub == "user-2"


class TestJWTRefreshTokenVerification:
    """Test verify_refresh_token with JWT-based tokens."""

    def test_valid_token_passes(self):
        """A freshly created token should verify successfully.

        The database stores the SHA-256 hash of the token, so we pass
        hash_refresh_token(token) as the first argument to simulate the DB lookup.
        """
        token, expires_at = create_refresh_token("user-123")
        assert verify_refresh_token(hash_refresh_token(token), token, expires_at) is True

    def test_verify_refresh_token_valid_token_passes(self):
        """Test that a valid refresh token passes verification."""
        user_id = "test-user-valid"
        token, expires_at = create_refresh_token(user_id)

        result = verify_refresh_token(hash_refresh_token(token), token, expires_at)
        assert result is True, "Valid refresh token should pass verification"

    def test_mismatched_stored_token_fails(self):
        """Providing a different token than stored should fail.

        stored_token_hash is the hash of token; provided is other_token.
        Hash(token) != Hash(other_token) so verification must fail.
        """
        token, expires_at = create_refresh_token("user-123")
        other_token, _ = create_refresh_token("user-456")
        assert verify_refresh_token(hash_refresh_token(token), other_token, expires_at) is False

    def test_verify_refresh_token_mismatched_tokens_fail(self):
        """Test that mismatched stored/provided tokens fail verification."""
        user_id1 = "test-user-1"
        user_id2 = "test-user-2"
        token1, expires_at1 = create_refresh_token(user_id1)
        token2, _ = create_refresh_token(user_id2)

        result = verify_refresh_token(hash_refresh_token(token1), token2, expires_at1)
        assert result is False, "Mismatched tokens should fail verification"

    def test_expired_db_timestamp_fails(self):
        """Token with expired DB timestamp should be rejected."""
        token, _ = create_refresh_token("user-123")
        expired = datetime.now(UTC) - timedelta(days=1)
        assert verify_refresh_token(hash_refresh_token(token), token, expired) is False

    def test_verify_refresh_token_expired_token_fails(self):
        """Test that expired tokens fail verification."""
        user_id = "test-user-expired"
        token, _ = create_refresh_token(user_id)

        # Set expiry to past
        expired_at = datetime.now(UTC) - timedelta(days=1)

        result = verify_refresh_token(hash_refresh_token(token), token, expired_at)
        assert result is False, "Expired token should fail verification"

    def test_none_stored_token_fails(self):
        """None stored token should be rejected."""
        assert (
            verify_refresh_token(None, "some-token", datetime.now(UTC) + timedelta(days=1)) is False
        )

    def test_verify_refresh_token_none_stored_token_fails(self):
        """Test that None stored token fails verification."""
        user_id = "test-user-none"
        token, expires_at = create_refresh_token(user_id)

        result = verify_refresh_token(None, token, expires_at)
        assert result is False, "None stored token should fail verification"

    def test_none_expires_at_fails(self):
        """None expiry should be rejected."""
        token, _ = create_refresh_token("user-123")
        assert verify_refresh_token(hash_refresh_token(token), token, None) is False

    def test_verify_refresh_token_none_expiry_fails(self):
        """Test that None expiry fails verification."""
        user_id = "test-user-noexpiry"
        token, _ = create_refresh_token(user_id)

        result = verify_refresh_token(hash_refresh_token(token), token, None)
        assert result is False, "None expiry should fail verification"

    def test_non_jwt_token_fails_verification(self):
        """An opaque string should fail JWT signature check.

        hash_refresh_token(opaque) is passed as stored_token_hash since that
        simulates how it would be stored; the JWT decode step must still reject it.
        """
        opaque = "not-a-jwt-token-just-random-string"
        future = datetime.now(UTC) + timedelta(days=7)
        assert verify_refresh_token(hash_refresh_token(opaque), opaque, future) is False

    def test_verify_refresh_token_non_jwt_fails(self):
        """Test that non-JWT tokens fail verification."""
        expires_at = datetime.now(UTC) + timedelta(days=7)
        fake_token = "not-a-jwt-token"

        result = verify_refresh_token(hash_refresh_token(fake_token), fake_token, expires_at)
        assert result is False, "Non-JWT token should fail verification"

    def test_access_token_fails_as_refresh(self):
        """An access token should fail refresh verification (wrong type)."""
        from app.security import create_access_token

        access = create_access_token({"sub": "user-123"})
        future = datetime.now(UTC) + timedelta(days=7)
        # access token has type="access", not "refresh"
        assert verify_refresh_token(hash_refresh_token(access), access, future) is False

    def test_verify_refresh_token_access_token_fails(self):
        """Test that access tokens fail refresh token verification."""
        from app.security import create_access_token

        # Create an access token (type='access')
        access_token = create_access_token({"sub": "test-user"})
        expires_at = datetime.now(UTC) + timedelta(days=7)

        result = verify_refresh_token(hash_refresh_token(access_token), access_token, expires_at)
        assert result is False, "Access token should fail refresh token verification"


class TestTokenRotation:
    """Test that token rotation produces valid new tokens."""

    def test_rotated_tokens_are_valid(self):
        """Both old and new rotation tokens should be valid JWTs."""
        old_token, old_exp = create_refresh_token("user-123")
        new_token, new_exp = create_refresh_token("user-123")
        # Both should verify independently (pass hash as stored_token_hash)
        assert verify_refresh_token(hash_refresh_token(old_token), old_token, old_exp) is True
        assert verify_refresh_token(hash_refresh_token(new_token), new_token, new_exp) is True

    def test_rotated_token_is_valid_jwt(self):
        """New refresh token should also be a valid JWT."""
        token, expires_at = create_refresh_token("user-123")
        assert verify_refresh_token(hash_refresh_token(token), token, expires_at) is True
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        assert payload.type == "refresh"
        assert payload.sub == "user-123"

    def test_rotated_tokens_are_different(self):
        """Test that newly created tokens after rotation are valid and different."""
        import time

        user_id = "test-user-rotation"

        # Create first token
        token1, expires1 = create_refresh_token(user_id)
        assert verify_refresh_token(hash_refresh_token(token1), token1, expires1) is True

        # Wait 1 second to ensure different iat (issued at) timestamp
        time.sleep(1)

        # Simulate rotation: create second token
        token2, expires2 = create_refresh_token(user_id)
        assert verify_refresh_token(hash_refresh_token(token2), token2, expires2) is True

        # Both tokens should be different (different iat means different signature)
        assert token1 != token2

        # First token should still be technically valid (until DB is updated)
        assert verify_refresh_token(hash_refresh_token(token1), token1, expires1) is True
