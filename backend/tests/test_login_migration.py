"""Integration tests for login with password migration.

Uses shared fixtures from conftest.py for database setup and client.
"""

from typing import Any

import pytest
from httpx import AsyncClient
from passlib.hash import pbkdf2_sha256
from sqlmodel import select

from app.models.user import User
from tests.conftest import get_test_engine

# Use shared fixtures from conftest.py (client, db_session, clean_database, etc.)


class TestLoginMigration:
    """Test suite for login endpoint with password migration."""

    @pytest.mark.asyncio
    async def test_login_migrates_legacy_password(
        self, client: AsyncClient, db_session: Any
    ):
        """Test that login migrates legacy pbkdf2 passwords to bcrypt."""
        # Create user with legacy pbkdf2 password hash
        email = "migrate@example.com"
        password = "test123"
        legacy_hash = pbkdf2_sha256.hash(password)

        user = User(
            email=email,
            hashed_password=legacy_hash,  # Directly set legacy hash
            full_name="Test User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Verify initial state
        assert user.hashed_password.startswith("$pbkdf2-sha256$")

        # Login with correct password
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )

        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data

        # Check that password was migrated in database
        # Need a new session since the API uses its own session
        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as new_session:
            result = await new_session.exec(select(User).where(User.email == email))
            updated_user = result.first()

            # Password should now be bcrypt
            assert updated_user.hashed_password.startswith("$2b$")
            assert updated_user.hashed_password != legacy_hash

            # Verify new password hash works
            from app.security import verify_password
            assert verify_password(password, updated_user.hashed_password) is True

    @pytest.mark.asyncio
    async def test_login_bcrypt_password_no_migration(
        self, client: AsyncClient, db_session
    ):
        """Test that login with bcrypt password doesn't trigger migration."""
        from app.security import hash_password

        # Create user with modern bcrypt password
        email = "modern@example.com"
        password = "test456"
        bcrypt_hash = hash_password(password)

        user = User(
            email=email,
            hashed_password=bcrypt_hash,
            full_name="Modern User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Verify initial state
        assert user.hashed_password.startswith("$2b$")

        # Login with correct password
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )

        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data

        # Check that password hash wasn't changed
        result = await db_session.exec(select(User).where(User.email == email))
        updated_user = result.first()

        # Password should still be the same bcrypt hash
        assert updated_user.hashed_password == bcrypt_hash

    @pytest.mark.asyncio
    async def test_login_legacy_wrong_password(
        self, client: AsyncClient, db_session
    ):
        """Test that login fails with wrong password for legacy hashes."""
        # Create user with legacy pbkdf2 password
        email = "wrong@example.com"
        password = "correct123"
        legacy_hash = pbkdf2_sha256.hash(password)

        user = User(
            email=email,
            hashed_password=legacy_hash,
            full_name="Wrong Password User",
        )
        db_session.add(user)
        await db_session.commit()

        # Try login with wrong password
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": "wrong_password"},
        )

        assert login_response.status_code == 401
        assert "Invalid credentials" in login_response.json()["detail"]

        # Password should not be migrated
        result = await db_session.exec(select(User).where(User.email == email))
        unchanged_user = result.first()
        assert unchanged_user.hashed_password == legacy_hash

    @pytest.mark.asyncio
    async def test_change_password_migrates_to_bcrypt(
        self, client: AsyncClient, db_session
    ):
        """Test that password change creates bcrypt hash even for legacy users."""

        # Create user with legacy pbkdf2 password
        email = "change@example.com"
        old_password = "old123"
        new_password = "new456"
        legacy_hash = pbkdf2_sha256.hash(old_password)

        user = User(
            email=email,
            hashed_password=legacy_hash,
            full_name="Change Password User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get auth token for password change
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": old_password},
        )
        token = login_response.json()["access_token"]

        # Change password
        change_response = await client.post(
            "/api/v1/users/me/change-password",
            json={
                "current_password": old_password,
                "new_password": new_password,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert change_response.status_code == 200

        # Check that new password is bcrypt
        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as new_session:
            result = await new_session.exec(select(User).where(User.email == email))
            updated_user = result.first()

            assert updated_user.hashed_password.startswith("$2b$")
            assert updated_user.hashed_password != legacy_hash

        # Verify new password works
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": new_password},
        )
        assert login_response.status_code == 200

        # Old password should not work
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": old_password},
        )
        assert login_response.status_code == 401

    @pytest.mark.asyncio
    async def test_new_user_uses_bcrypt(
        self, client: AsyncClient, db_session
    ):
        """Test that new users are created with bcrypt passwords."""
        email = "newuser@example.com"
        password = "newuser123"

        # Register new user
        register_response = await client.post(
            "/api/v1/users/register",
            json={
                "email": email,
                "password": password,
                "full_name": "New User",
            },
        )

        assert register_response.status_code == 201

        # Check that password is bcrypt (need new session since API creates user in its own session)
        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as new_session:
            result = await new_session.exec(select(User).where(User.email == email))
            new_user = result.first()

            assert new_user.hashed_password.startswith("$2b$")

        # Verify login works
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_last_login_updated_with_migration(
        self, client: AsyncClient, db_session
    ):
        """Test that last_login_at is updated when password is migrated."""
        import datetime
        from zoneinfo import ZoneInfo

        # Create user with legacy password
        email = "login_time@example.com"
        password = "test123"
        legacy_hash = pbkdf2_sha256.hash(password)

        user = User(
            email=email,
            hashed_password=legacy_hash,
            full_name="Login Time User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Initially no last_login
        assert user.last_login_at is None

        # Login
        before_login = datetime.datetime.now(ZoneInfo("UTC"))
        login_response = await client.post(
            "/api/v1/users/login",
            json={"email": email, "password": password},
        )
        after_login = datetime.datetime.now(ZoneInfo("UTC"))

        assert login_response.status_code == 200

        # Check last_login was updated
        _, TestSessionLocal = get_test_engine()
        async with TestSessionLocal() as new_session:
            result = await new_session.exec(select(User).where(User.email == email))
            updated_user = result.first()

            assert updated_user.last_login_at is not None
            assert before_login <= updated_user.last_login_at <= after_login
            # Password should also be migrated
            assert updated_user.hashed_password.startswith("$2b$")
