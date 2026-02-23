"""Tests for API key management."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.api_key import APIKeyScope
from app.services import api_key_service


class TestAPIKeyGeneration:
    """Test API key generation and hashing."""

    def test_generate_api_key_format(self):
        """Test that generated API keys have the correct format."""
        key = api_key_service.generate_api_key()

        assert key.startswith("is_")
        assert len(key) == 43  # is_ (3) + 40 random chars
        # URL-safe base64 uses A-Za-z0-9_- characters
        assert all(c.isalnum() or c in "_-" for c in key[3:])

    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique."""
        keys = {api_key_service.generate_api_key() for _ in range(100)}
        assert len(keys) == 100  # All unique

    def test_hash_and_verify_api_key(self):
        """Test API key hashing and verification."""
        key = api_key_service.generate_api_key()
        key_hash = api_key_service.hash_api_key(key)

        # Hash should be bcrypt format
        assert key_hash.startswith("$2b$")

        # Should verify correctly
        assert api_key_service.verify_api_key(key, key_hash)

        # Should not verify with wrong key
        wrong_key = api_key_service.generate_api_key()
        assert not api_key_service.verify_api_key(wrong_key, key_hash)

    def test_hash_different_each_time(self):
        """Test that hashing the same key produces different hashes (due to salt)."""
        key = api_key_service.generate_api_key()
        hash1 = api_key_service.hash_api_key(key)
        hash2 = api_key_service.hash_api_key(key)

        # Hashes should be different (different salts)
        assert hash1 != hash2

        # But both should verify correctly
        assert api_key_service.verify_api_key(key, hash1)
        assert api_key_service.verify_api_key(key, hash2)


@pytest.mark.asyncio
class TestAPIKeyService:
    """Test API key service functions."""

    async def test_create_api_key(self, session, test_user):
        """Test creating an API key."""
        from app.models.api_key import APIKeyCreate

        key_data = APIKeyCreate(
            name="Test Key",
            scopes=[APIKeyScope.READ, APIKeyScope.WRITE],
            rate_limit=100,
        )

        plain_key, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Check plain key format
        assert plain_key.startswith("is_")
        assert len(plain_key) == 43

        # Check stored key
        assert api_key.user_id == test_user.id
        assert api_key.name == "Test Key"
        assert api_key.key_prefix == plain_key[:8]
        assert api_key.scopes == "read,write"
        assert api_key.rate_limit == 100
        assert api_key.is_active is True
        assert api_key.request_count == 0

        # Verify the key works
        assert api_key_service.verify_api_key(plain_key, api_key.key_hash)

    async def test_create_api_key_invalid_user(self, session):
        """Test creating API key for non-existent user."""
        from app.models.api_key import APIKeyCreate

        key_data = APIKeyCreate(name="Test Key")
        invalid_user_id = uuid4()

        with pytest.raises(ValueError, match="User not found"):
            await api_key_service.create_api_key(session, invalid_user_id, key_data)

    async def test_create_api_key_limit(self, session, test_user):
        """Test that users can't create more than 10 API keys."""
        from app.models.api_key import APIKeyCreate

        # Create 10 keys
        for i in range(10):
            key_data = APIKeyCreate(name=f"Key {i}")
            await api_key_service.create_api_key(session, test_user.id, key_data)

        # 11th should fail
        key_data = APIKeyCreate(name="Key 11")
        with pytest.raises(ValueError, match="Maximum number of API keys"):
            await api_key_service.create_api_key(session, test_user.id, key_data)

    async def test_get_user_api_keys(self, session, test_user):
        """Test retrieving user's API keys."""
        from app.models.api_key import APIKeyCreate

        # Create some keys
        for i in range(3):
            key_data = APIKeyCreate(name=f"Key {i}")
            await api_key_service.create_api_key(session, test_user.id, key_data)

        # Retrieve keys
        keys = await api_key_service.get_user_api_keys(session, test_user.id)

        assert len(keys) == 3
        # Should be sorted by creation date (newest first)
        assert keys[0].name == "Key 2"
        assert keys[1].name == "Key 1"
        assert keys[2].name == "Key 0"

    async def test_update_api_key(self, session, test_user):
        """Test updating an API key."""
        from app.models.api_key import APIKeyCreate, APIKeyUpdate

        # Create key
        key_data = APIKeyCreate(name="Original Name", rate_limit=60)
        _, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Update key
        update_data = APIKeyUpdate(
            name="Updated Name",
            scopes=[APIKeyScope.READ],
            rate_limit=120,
            is_active=False,
        )
        updated_key = await api_key_service.update_api_key(
            session, api_key.id, test_user.id, update_data
        )

        assert updated_key is not None
        assert updated_key.name == "Updated Name"
        assert updated_key.scopes == "read"
        assert updated_key.rate_limit == 120
        assert updated_key.is_active is False

    async def test_update_api_key_wrong_user(self, session, test_user, session_factory):
        """Test that users can't update other users' keys."""
        from app.models.api_key import APIKeyCreate, APIKeyUpdate
        from app.models.user import User

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
        )
        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)

        # Create key for test_user
        key_data = APIKeyCreate(name="Test Key")
        _, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Try to update with other_user's ID
        update_data = APIKeyUpdate(name="Hacked")
        updated_key = await api_key_service.update_api_key(
            session, api_key.id, other_user.id, update_data
        )

        # Should return None (not found)
        assert updated_key is None

    async def test_delete_api_key(self, session, test_user):
        """Test deleting an API key."""
        from app.models.api_key import APIKeyCreate

        # Create key
        key_data = APIKeyCreate(name="To Delete")
        _, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Delete key
        deleted = await api_key_service.delete_api_key(session, api_key.id, test_user.id)
        assert deleted is True

        # Should not be retrievable
        key = await api_key_service.get_api_key_by_id(session, api_key.id, test_user.id)
        assert key is None

    async def test_verify_api_key_and_get_user(self, session, test_user):
        """Test verifying an API key and retrieving the user."""
        from app.models.api_key import APIKeyCreate

        # Create key
        key_data = APIKeyCreate(name="Test Key")
        plain_key, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Verify key and get user
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

        # Check that usage was recorded
        await session.refresh(api_key)
        assert api_key.request_count == 1
        assert api_key.last_used_at is not None

    async def test_verify_invalid_api_key(self, session):
        """Test verifying an invalid API key."""
        # Wrong prefix
        user = await api_key_service.verify_api_key_and_get_user(session, "wrong_key")
        assert user is None

        # Valid format but doesn't exist
        fake_key = api_key_service.generate_api_key()
        user = await api_key_service.verify_api_key_and_get_user(session, fake_key)
        assert user is None

    async def test_verify_expired_api_key(self, session, test_user):
        """Test that expired API keys are rejected."""
        from app.models.api_key import APIKeyCreate

        # Create expired key
        key_data = APIKeyCreate(
            name="Expired Key",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        plain_key, _ = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Should be rejected
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None

    async def test_verify_inactive_api_key(self, session, test_user):
        """Test that inactive API keys are rejected."""
        from app.models.api_key import APIKeyCreate, APIKeyUpdate

        # Create key
        key_data = APIKeyCreate(name="Test Key")
        plain_key, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Deactivate key
        update_data = APIKeyUpdate(is_active=False)
        await api_key_service.update_api_key(session, api_key.id, test_user.id, update_data)

        # Should be rejected
        user = await api_key_service.verify_api_key_and_get_user(session, plain_key)
        assert user is None


@pytest.mark.asyncio
class TestAPIKeyEndpoints:
    """Test API key management endpoints."""

    async def test_create_api_key_endpoint(self, client, auth_headers):
        """Test POST /api/v1/api-keys/."""
        response = await client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test Key",
                "scopes": ["read", "write"],
                "rate_limit": 100,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "key" in data
        assert "api_key" in data

        # Check plain key
        assert data["key"].startswith("is_")
        assert len(data["key"]) == 43

        # Check API key details
        api_key = data["api_key"]
        assert api_key["name"] == "Test Key"
        assert api_key["scopes"] == "read,write"
        assert api_key["rate_limit"] == 100
        assert api_key["is_active"] is True

    async def test_list_api_keys_endpoint(self, client, auth_headers, session, test_user):
        """Test GET /api/v1/api-keys/."""
        from app.models.api_key import APIKeyCreate

        # Create some keys
        for i in range(3):
            key_data = APIKeyCreate(name=f"Key {i}")
            await api_key_service.create_api_key(session, test_user.id, key_data)

        response = await client.get("/api/v1/api-keys/", headers=auth_headers)

        assert response.status_code == 200
        keys = response.json()
        assert len(keys) == 3

    async def test_get_api_key_endpoint(self, client, auth_headers, session, test_user):
        """Test GET /api/v1/api-keys/{key_id}."""
        from app.models.api_key import APIKeyCreate

        # Create key
        key_data = APIKeyCreate(name="Test Key")
        _, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        response = await client.get(
            f"/api/v1/api-keys/{api_key.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(api_key.id)
        assert data["name"] == "Test Key"

    async def test_update_api_key_endpoint(self, client, auth_headers, session, test_user):
        """Test PATCH /api/v1/api-keys/{key_id}."""
        from app.models.api_key import APIKeyCreate

        # Create key
        key_data = APIKeyCreate(name="Original")
        _, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        response = await client.patch(
            f"/api/v1/api-keys/{api_key.id}",
            json={"name": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"

    async def test_delete_api_key_endpoint(self, client, auth_headers, session, test_user):
        """Test DELETE /api/v1/api-keys/{key_id}."""
        from app.models.api_key import APIKeyCreate

        # Create key
        key_data = APIKeyCreate(name="To Delete")
        _, api_key = await api_key_service.create_api_key(session, test_user.id, key_data)

        response = await client.delete(
            f"/api/v1/api-keys/{api_key.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        keys = await api_key_service.get_user_api_keys(session, test_user.id)
        assert len(keys) == 0

    async def test_api_key_authentication(self, client, session, test_user):
        """Test that API keys can be used for authentication."""
        from app.models.api_key import APIKeyCreate

        # Create API key
        key_data = APIKeyCreate(name="Auth Test", scopes=[APIKeyScope.READ])
        plain_key, _ = await api_key_service.create_api_key(session, test_user.id, key_data)

        # Use API key to access protected endpoint
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {plain_key}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    async def test_invalid_api_key_authentication(self, client):
        """Test that invalid API keys are rejected."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer is_invalid_key_xxxxxxxxxxxxxxxxxxxxxxxxxx"},
        )

        assert response.status_code == 401

    async def test_unauthorized_access_other_user_key(
        self, client, auth_headers, session, test_user
    ):
        """Test that users can't access other users' API keys."""
        from app.models.api_key import APIKeyCreate
        from app.models.user import User

        # Create another user
        other_user = User(email="other@example.com", hashed_password="hashed")
        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)

        # Create key for other user
        key_data = APIKeyCreate(name="Other's Key")
        _, other_key = await api_key_service.create_api_key(session, other_user.id, key_data)

        # Try to access with test_user's auth
        response = await client.get(
            f"/api/v1/api-keys/{other_key.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
