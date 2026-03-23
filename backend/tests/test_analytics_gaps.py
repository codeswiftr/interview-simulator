"""Gap tests for analytics API — tests not covered in existing test files.

Tests to add:
- test_get_analytics_summary_service_error_propagates_as_500
- test_get_user_progress_service_called_once
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.analytics import get_analytics_summary, get_user_progress


def _mock_session():
    """Return a fully-mocked AsyncSession."""
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _mock_user(user_id=None):
    """Return a MagicMock that behaves like a User model instance."""
    user = MagicMock()
    user.id = user_id or uuid4()
    return user


class TestGetAnalyticsSummaryErrorHandling:
    """Tests for service error propagation in get_analytics_summary."""

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_get_analytics_summary_service_error_propagates_as_500(self, mock_service_cls):
        """Service exceptions should propagate as HTTP 500."""
        session = _mock_session()
        user = _mock_user()

        mock_service = MagicMock()
        mock_service.get_analytics_summary = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        mock_service_cls.return_value = mock_service

        with pytest.raises(Exception) as exc_info:
            await get_analytics_summary(user, session)

        assert "Database connection failed" in str(exc_info.value)


class TestGetUserProgressServiceCalls:
    """Tests for service call verification in get_user_progress."""

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_get_user_progress_service_called_once(self, mock_service_cls):
        """Service should be called exactly once per request."""
        session = _mock_session()
        user = _mock_user()

        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=[])
        mock_service_cls.return_value = mock_service

        await get_user_progress(user, session)

        mock_service.get_user_progress.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.api.analytics.BehavioralAnalyticsService")
    async def test_get_user_progress_service_called_with_correct_args(self, mock_service_cls):
        """Service should be called with db session and user.id."""
        session = _mock_session()
        user = _mock_user()

        mock_service = MagicMock()
        mock_service.get_user_progress = AsyncMock(return_value=[])
        mock_service_cls.return_value = mock_service

        await get_user_progress(user, session)

        mock_service.get_user_progress.assert_awaited_once_with(session, user.id)
