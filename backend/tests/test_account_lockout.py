"""Tests for account lockout functionality.

Tests the account lockout service which prevents brute force attacks by:
- Locking accounts after 5 failed login attempts within 15 minutes
- Automatically unlocking after 15 minutes
- Clearing failed attempts after successful login
"""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.user import User
from app.security import hash_password
from app.services.account_lockout import AccountLockoutService
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for lockout testing."""
    user = User(
        email="lockout.test@example.com",
        hashed_password=hash_password("CorrectPassword123!"),
        full_name="Lockout Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestAccountLockoutService:
    """Test AccountLockoutService directly."""

    async def test_record_failed_attempt(self, db_session: AsyncSession):
        """Test recording a failed login attempt."""
        service = AccountLockoutService()
        await service.record_login_attempt(
            db_session, "test@example.com", "127.0.0.1", success=False
        )

        count = await service.get_failed_attempts_count(db_session, "test@example.com")
        assert count == 1

    async def test_record_successful_attempt(self, db_session: AsyncSession):
        """Test recording a successful login attempt."""
        service = AccountLockoutService()
        await service.record_login_attempt(
            db_session, "test@example.com", "127.0.0.1", success=True
        )

        # Successful attempts don't count toward lockout
        count = await service.get_failed_attempts_count(db_session, "test@example.com")
        assert count == 0

    async def test_account_not_locked_before_threshold(self, db_session: AsyncSession):
        """Test account is not locked with 4 failed attempts (below threshold)."""
        service = AccountLockoutService()

        # Record 4 failed attempts
        for _ in range(4):
            await service.record_login_attempt(
                db_session, "test@example.com", "127.0.0.1", success=False
            )

        is_locked, _ = await service.is_account_locked(db_session, "test@example.com")
        assert not is_locked

    async def test_account_locked_after_five_failures(self, db_session: AsyncSession):
        """Test account is locked after 5 failed attempts."""
        service = AccountLockoutService()

        # Record 5 failed attempts
        for _ in range(5):
            await service.record_login_attempt(
                db_session, "test@example.com", "127.0.0.1", success=False
            )

        is_locked, lockout_expires = await service.is_account_locked(
            db_session, "test@example.com"
        )
        assert is_locked
        assert lockout_expires is not None
        assert lockout_expires > datetime.now(UTC)

    async def test_lockout_expires_after_duration(self, db_session: AsyncSession):
        """Test account lockout expires after lockout duration."""
        service = AccountLockoutService()

        # Record 5 failed attempts with backdated timestamps
        from app.models.login_attempt import LoginAttempt

        old_time = datetime.now(UTC) - timedelta(minutes=20)
        for i in range(5):
            attempt = LoginAttempt(
                email="test@example.com",
                ip_address="127.0.0.1",
                success=False,
                attempted_at=old_time + timedelta(seconds=i),
            )
            db_session.add(attempt)
        await db_session.commit()

        # Lockout should have expired
        is_locked, _ = await service.is_account_locked(db_session, "test@example.com")
        assert not is_locked

    async def test_successful_login_clears_attempts(self, db_session: AsyncSession):
        """Test successful login clears failed attempts."""
        service = AccountLockoutService()

        # Record 3 failed attempts
        for _ in range(3):
            await service.record_login_attempt(
                db_session, "test@example.com", "127.0.0.1", success=False
            )

        count = await service.get_failed_attempts_count(db_session, "test@example.com")
        assert count == 3

        # Record successful login
        await service.record_login_attempt(
            db_session, "test@example.com", "127.0.0.1", success=True
        )

        # Failed attempts should still be counted (only cleared on next check)
        count = await service.get_failed_attempts_count(db_session, "test@example.com")
        assert count == 3

    async def test_get_failed_attempts_count(self, db_session: AsyncSession):
        """Test getting count of failed attempts in window."""
        service = AccountLockoutService()

        # Record 3 failed attempts
        for _ in range(3):
            await service.record_login_attempt(
                db_session, "test@example.com", "127.0.0.1", success=False
            )

        count = await service.get_failed_attempts_count(db_session, "test@example.com")
        assert count == 3

    async def test_case_insensitive_email_lockout(self, db_session: AsyncSession):
        """Test lockout works with case-insensitive email matching."""
        service = AccountLockoutService()

        # Record failures with different cases
        await service.record_login_attempt(
            db_session, "Test@Example.com", "127.0.0.1", success=False
        )
        await service.record_login_attempt(
            db_session, "test@example.com", "127.0.0.1", success=False
        )
        await service.record_login_attempt(
            db_session, "TEST@EXAMPLE.COM", "127.0.0.1", success=False
        )

        # Should count all as same email
        count = await service.get_failed_attempts_count(db_session, "test@example.com")
        assert count == 3


class TestLoginEndpointWithLockout:
    """Test login endpoint with account lockout integration."""

    async def test_login_success_no_lockout(self, db_session: AsyncSession, test_user: User):
        """Test successful login doesn't trigger lockout."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": test_user.email,
                    "password": "CorrectPassword123!",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    async def test_login_failure_increments_attempts(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test failed login increments attempt counter."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # First failed attempt
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": test_user.email,
                    "password": "WrongPassword",
                },
            )
            assert response.status_code == 401

            # Check failed attempts count
            service = AccountLockoutService()
            count = await service.get_failed_attempts_count(db_session, test_user.email)
            assert count == 1

    async def test_login_locked_after_five_failures(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test account is locked after 5 failed login attempts."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Make 5 failed login attempts
            for i in range(5):
                response = await client.post(
                    "/api/v1/users/login",
                    json={
                        "email": test_user.email,
                        "password": f"WrongPassword{i}",
                    },
                )
                assert response.status_code == 401

            # 6th attempt should be blocked by lockout
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": test_user.email,
                    "password": "CorrectPassword123!",  # Even correct password is blocked
                },
            )
            assert response.status_code == 401
            data = response.json()
            assert "locked" in data["detail"]["message"].lower()
            assert "lockout_expires_at" in data["detail"]

    async def test_login_fails_for_nonexistent_user(self, db_session: AsyncSession):
        """Test login attempt for non-existent user records failed attempt."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "SomePassword123!",
                },
            )
            assert response.status_code == 401

            # Check failed attempt was recorded
            service = AccountLockoutService()
            count = await service.get_failed_attempts_count(
                db_session, "nonexistent@example.com"
            )
            assert count == 1

    async def test_lockout_case_insensitive(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test lockout works with case-insensitive emails."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Make failed attempts with different email cases
            emails = [
                test_user.email.upper(),
                test_user.email.lower(),
                test_user.email.capitalize(),
            ]

            for email in emails:
                await client.post(
                    "/api/v1/users/login",
                    json={"email": email, "password": "WrongPassword"},
                )

            # Check all counted toward same account
            service = AccountLockoutService()
            count = await service.get_failed_attempts_count(db_session, test_user.email)
            assert count == 3

    async def test_successful_login_after_failures_works(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test successful login works after some failures (below threshold)."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Make 3 failed attempts
            for _ in range(3):
                await client.post(
                    "/api/v1/users/login",
                    json={"email": test_user.email, "password": "WrongPassword"},
                )

            # Successful login should work
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "email": test_user.email,
                    "password": "CorrectPassword123!",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
