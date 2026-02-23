"""Unit tests for app/services/account_lockout.py."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.account_lockout import AccountLockoutService


class TestAccountLockoutInit:
    """Tests for AccountLockoutService initialization."""

    def test_default_config(self):
        service = AccountLockoutService()
        assert service.max_attempts == 5
        assert service.window_minutes == 15
        assert service.lockout_minutes == 15


class TestRecordLoginAttempt:
    """Tests for recording login attempts."""

    @pytest.mark.asyncio
    async def test_records_failed_attempt(self):
        service = AccountLockoutService()
        session = AsyncMock()

        await service.record_login_attempt(session, "User@Test.com", "1.2.3.4", success=False)

        session.add.assert_called_once()
        attempt = session.add.call_args[0][0]
        assert attempt.email == "user@test.com"  # lowercased
        assert attempt.ip_address == "1.2.3.4"
        assert attempt.success is False
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_successful_attempt_triggers_cleanup(self):
        service = AccountLockoutService()
        session = AsyncMock()

        # Mock cleanup query returning no old attempts
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.exec.return_value = mock_result

        await service.record_login_attempt(session, "user@test.com", "1.2.3.4", success=True)

        session.add.assert_called_once()
        # Cleanup should have been called (session.exec for the old-attempts query)
        session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_attempt_skips_cleanup(self):
        service = AccountLockoutService()
        session = AsyncMock()

        await service.record_login_attempt(session, "user@test.com", "1.2.3.4", success=False)

        # No exec call — cleanup only happens on success
        session.exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_normalized_to_lowercase(self):
        service = AccountLockoutService()
        session = AsyncMock()

        await service.record_login_attempt(session, "JOE@EXAMPLE.COM", "10.0.0.1", success=False)

        attempt = session.add.call_args[0][0]
        assert attempt.email == "joe@example.com"


class TestIsAccountLocked:
    """Tests for account lockout checking."""

    @pytest.mark.asyncio
    async def test_not_locked_with_few_failures(self):
        service = AccountLockoutService()
        session = AsyncMock()

        # 3 failed attempts — below threshold of 5
        mock_result = MagicMock()
        mock_result.all.return_value = [MagicMock() for _ in range(3)]
        session.exec.return_value = mock_result

        is_locked, expires_at = await service.is_account_locked(session, "user@test.com")

        assert is_locked is False
        assert expires_at is None

    @pytest.mark.asyncio
    async def test_locked_with_5_recent_failures(self):
        service = AccountLockoutService()
        session = AsyncMock()

        # 5 failed attempts, most recent just now
        now = datetime.now(UTC)
        attempts = []
        for i in range(5):
            attempt = MagicMock()
            attempt.attempted_at = now - timedelta(minutes=i)
            attempts.append(attempt)

        mock_result = MagicMock()
        mock_result.all.return_value = attempts
        session.exec.return_value = mock_result

        is_locked, expires_at = await service.is_account_locked(session, "user@test.com")

        assert is_locked is True
        assert expires_at is not None
        # 5th attempt is at now - 4 minutes, lockout = 15 minutes from that
        expected_expiry = attempts[4].attempted_at + timedelta(minutes=15)
        assert expires_at == expected_expiry

    @pytest.mark.asyncio
    async def test_lockout_expired(self):
        service = AccountLockoutService()
        session = AsyncMock()

        # 5 failed attempts all 20 minutes ago — lockout should have expired
        old_time = datetime.now(UTC) - timedelta(minutes=20)
        attempts = []
        for i in range(5):
            attempt = MagicMock()
            attempt.attempted_at = old_time - timedelta(seconds=i)
            attempts.append(attempt)

        mock_result = MagicMock()
        mock_result.all.return_value = attempts
        session.exec.return_value = mock_result

        is_locked, expires_at = await service.is_account_locked(session, "user@test.com")

        assert is_locked is False
        assert expires_at is None

    @pytest.mark.asyncio
    async def test_zero_failed_attempts(self):
        service = AccountLockoutService()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.exec.return_value = mock_result

        is_locked, expires_at = await service.is_account_locked(session, "user@test.com")

        assert is_locked is False
        assert expires_at is None


class TestGetFailedAttemptsCount:
    """Tests for counting failed attempts."""

    @pytest.mark.asyncio
    async def test_returns_count(self):
        service = AccountLockoutService()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = [MagicMock(), MagicMock(), MagicMock()]
        session.exec.return_value = mock_result

        count = await service.get_failed_attempts_count(session, "user@test.com")
        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_attempts(self):
        service = AccountLockoutService()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.exec.return_value = mock_result

        count = await service.get_failed_attempts_count(session, "user@test.com")
        assert count == 0


class TestClearFailedAttempts:
    """Tests for clearing failed attempts after successful login."""

    @pytest.mark.asyncio
    async def test_deletes_all_recent_attempts(self):
        service = AccountLockoutService()
        session = AsyncMock()

        attempt1 = MagicMock()
        attempt2 = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [attempt1, attempt2]
        session.exec.return_value = mock_result

        await service.clear_failed_attempts(session, "user@test.com")

        assert session.delete.call_count == 2
        session.delete.assert_any_call(attempt1)
        session.delete.assert_any_call(attempt2)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_attempts_to_clear(self):
        service = AccountLockoutService()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.exec.return_value = mock_result

        await service.clear_failed_attempts(session, "user@test.com")

        session.delete.assert_not_called()
        session.commit.assert_called_once()


class TestCleanupOldAttempts:
    """Tests for the cleanup of old attempts."""

    @pytest.mark.asyncio
    async def test_deletes_attempts_older_than_24h(self):
        service = AccountLockoutService()
        session = AsyncMock()

        old_attempt = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [old_attempt]
        session.exec.return_value = mock_result

        await service._cleanup_old_attempts(session, "user@test.com")

        session.delete.assert_called_once_with(old_attempt)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_nothing_to_cleanup(self):
        service = AccountLockoutService()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.exec.return_value = mock_result

        await service._cleanup_old_attempts(session, "user@test.com")

        session.delete.assert_not_called()
        session.commit.assert_called_once()
