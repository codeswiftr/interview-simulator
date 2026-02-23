"""Pure unit tests for AccountLockoutService.

Tests all methods with mocked AsyncSession. No database required.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.account_lockout import (
    LOCKOUT_DURATION_MINUTES,
    LOCKOUT_WINDOW_MINUTES,
    MAX_FAILED_ATTEMPTS,
    AccountLockoutService,
)


@pytest.fixture
def service():
    return AccountLockoutService()


@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session


class TestAccountLockoutInit:
    def test_default_values(self, service):
        assert service.max_attempts == MAX_FAILED_ATTEMPTS
        assert service.window_minutes == LOCKOUT_WINDOW_MINUTES
        assert service.lockout_minutes == LOCKOUT_DURATION_MINUTES

    def test_constants(self):
        assert MAX_FAILED_ATTEMPTS == 5
        assert LOCKOUT_WINDOW_MINUTES == 15
        assert LOCKOUT_DURATION_MINUTES == 15


class TestRecordLoginAttempt:
    @pytest.mark.asyncio
    async def test_records_failed_attempt(self, service, mock_session):
        await service.record_login_attempt(mock_session, "Test@Example.com", "1.2.3.4", False)
        mock_session.add.assert_called_once()
        attempt = mock_session.add.call_args[0][0]
        assert attempt.email == "test@example.com"
        assert attempt.ip_address == "1.2.3.4"
        assert attempt.success is False
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_records_successful_attempt_and_cleans_up(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        await service.record_login_attempt(mock_session, "user@test.com", "1.2.3.4", True)
        mock_session.add.assert_called_once()
        attempt = mock_session.add.call_args[0][0]
        assert attempt.success is True
        # commit called: once for add, once for cleanup
        assert mock_session.commit.await_count == 2

    @pytest.mark.asyncio
    async def test_email_lowercased(self, service, mock_session):
        await service.record_login_attempt(mock_session, "USER@DOMAIN.COM", "10.0.0.1", False)
        attempt = mock_session.add.call_args[0][0]
        assert attempt.email == "user@domain.com"

    @pytest.mark.asyncio
    async def test_attempted_at_set(self, service, mock_session):
        before = datetime.now(UTC)
        await service.record_login_attempt(mock_session, "u@t.com", "1.1.1.1", False)
        after = datetime.now(UTC)
        attempt = mock_session.add.call_args[0][0]
        assert before <= attempt.attempted_at <= after

    @pytest.mark.asyncio
    async def test_no_cleanup_on_failure(self, service, mock_session):
        await service.record_login_attempt(mock_session, "u@t.com", "1.1.1.1", False)
        mock_session.exec.assert_not_awaited()


class TestIsAccountLocked:
    @pytest.mark.asyncio
    async def test_not_locked_below_threshold(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = [MagicMock() for _ in range(3)]
        mock_session.exec.return_value = mock_result

        locked, expires = await service.is_account_locked(mock_session, "u@t.com")
        assert locked is False
        assert expires is None

    @pytest.mark.asyncio
    async def test_not_locked_zero_attempts(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        locked, expires = await service.is_account_locked(mock_session, "u@t.com")
        assert locked is False
        assert expires is None

    @pytest.mark.asyncio
    async def test_locked_at_threshold(self, service, mock_session):
        now = datetime.now(UTC)
        fifth_attempt = MagicMock()
        fifth_attempt.attempted_at = now - timedelta(minutes=1)

        attempts = [MagicMock() for _ in range(4)] + [fifth_attempt]
        mock_result = MagicMock()
        mock_result.all.return_value = attempts
        mock_session.exec.return_value = mock_result

        locked, expires = await service.is_account_locked(mock_session, "u@t.com")
        assert locked is True
        assert expires == fifth_attempt.attempted_at + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    @pytest.mark.asyncio
    async def test_lockout_expired(self, service, mock_session):
        fifth_attempt = MagicMock()
        fifth_attempt.attempted_at = datetime.now(UTC) - timedelta(minutes=20)

        attempts = [MagicMock() for _ in range(4)] + [fifth_attempt]
        mock_result = MagicMock()
        mock_result.all.return_value = attempts
        mock_session.exec.return_value = mock_result

        locked, expires = await service.is_account_locked(mock_session, "u@t.com")
        assert locked is False
        assert expires is None

    @pytest.mark.asyncio
    async def test_email_lowercased(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        await service.is_account_locked(mock_session, "USER@TEST.COM")
        # Verify the query was built (exec was called)
        mock_session.exec.assert_awaited_once()


class TestGetFailedAttemptsCount:
    @pytest.mark.asyncio
    async def test_returns_count(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_session.exec.return_value = mock_result

        count = await service.get_failed_attempts_count(mock_session, "u@t.com")
        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_zero_no_attempts(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        count = await service.get_failed_attempts_count(mock_session, "u@t.com")
        assert count == 0

    @pytest.mark.asyncio
    async def test_email_lowercased(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        await service.get_failed_attempts_count(mock_session, "UPPER@CASE.COM")
        mock_session.exec.assert_awaited_once()


class TestClearFailedAttempts:
    @pytest.mark.asyncio
    async def test_deletes_all_attempts(self, service, mock_session):
        attempts = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.all.return_value = attempts
        mock_session.exec.return_value = mock_result

        await service.clear_failed_attempts(mock_session, "u@t.com")
        assert mock_session.delete.await_count == 2
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_attempts_to_clear(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        await service.clear_failed_attempts(mock_session, "u@t.com")
        mock_session.delete.assert_not_awaited()
        mock_session.commit.assert_awaited_once()


class TestCleanupOldAttempts:
    @pytest.mark.asyncio
    async def test_deletes_old_attempts(self, service, mock_session):
        old_attempts = [MagicMock(), MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.all.return_value = old_attempts
        mock_session.exec.return_value = mock_result

        await service._cleanup_old_attempts(mock_session, "u@t.com")
        assert mock_session.delete.await_count == 3
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_nothing_to_clean(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        await service._cleanup_old_attempts(mock_session, "u@t.com")
        mock_session.delete.assert_not_awaited()
        mock_session.commit.assert_awaited_once()
