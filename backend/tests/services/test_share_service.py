"""Tests for share service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus, InterviewType
from app.models.interview_share import InterviewShare, SharedInterviewRead
from app.models.user import User
from app.services.share_service import ShareService


class TestShareServiceCreateLink:
    """Tests for creating share links."""

    @pytest.mark.asyncio
    async def test_create_share_link_interview_not_found(self):
        """Should raise ValueError if interview doesn't exist."""
        service = ShareService()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Interview .* not found"):
            await service.create_share_link(mock_session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_create_share_link_access_denied(self):
        """Should raise ValueError if user doesn't own interview."""
        service = ShareService()
        mock_session = AsyncMock()

        interview = InterviewSession(
            id=uuid4(),
            user_id=uuid4(),  # Different user
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        mock_result = MagicMock()
        mock_result.first.return_value = interview
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="access denied"):
            await service.create_share_link(mock_session, interview.id, uuid4())

    @pytest.mark.asyncio
    async def test_create_share_link_returns_existing(self):
        """Should return existing active share if one exists."""
        service = ShareService()
        user_id = uuid4()
        interview_id = uuid4()

        interview = InterviewSession(
            id=interview_id,
            user_id=user_id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        existing_share = InterviewShare(
            id=uuid4(),
            interview_id=interview_id,
            created_by=user_id,
            token="existing_token_123",
            expires_at=datetime.now(UTC) + timedelta(days=3),
        )

        mock_session = AsyncMock()

        call_count = 0
        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()

            if call_count == 1:  # Interview query
                result.first.return_value = interview
            elif call_count == 2:  # Existing share query
                result.first.return_value = existing_share

            return result

        mock_session.exec = mock_exec

        result = await service.create_share_link(mock_session, interview_id, user_id)

        assert result.token == "existing_token_123"
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_link_creates_new(self):
        """Should create new share if none exists."""
        service = ShareService()
        user_id = uuid4()
        interview_id = uuid4()

        interview = InterviewSession(
            id=interview_id,
            user_id=user_id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        mock_session = AsyncMock()

        call_count = 0
        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()

            if call_count == 1:  # Interview query
                result.first.return_value = interview
            elif call_count == 2:  # Existing share query
                result.first.return_value = None  # No existing share

            return result

        mock_session.exec = mock_exec

        result = await service.create_share_link(mock_session, interview_id, user_id)

        assert result.interview_id == interview_id
        assert result.created_by == user_id
        assert result.token is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestShareServiceGetSharedInterview:
    """Tests for retrieving shared interview data."""

    @pytest.mark.asyncio
    async def test_get_shared_interview_token_not_found(self):
        """Should raise ValueError if token doesn't exist."""
        service = ShareService()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Share link not found"):
            await service.get_shared_interview(mock_session, "invalid_token")

    @pytest.mark.asyncio
    async def test_get_shared_interview_expired_token(self):
        """Should raise ValueError if share link has expired."""
        service = ShareService()

        expired_share = InterviewShare(
            id=uuid4(),
            interview_id=uuid4(),
            created_by=uuid4(),
            token="expired_token",
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = expired_share
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="expired"):
            await service.get_shared_interview(mock_session, "expired_token")

    @pytest.mark.asyncio
    async def test_get_shared_interview_increments_view_count(self):
        """Should increment view count on valid access."""
        service = ShareService()
        user_id = uuid4()
        interview_id = uuid4()

        share = InterviewShare(
            id=uuid4(),
            interview_id=interview_id,
            created_by=user_id,
            token="valid_token",
            expires_at=datetime.now(UTC) + timedelta(days=3),
            view_count=5,
        )

        interview = InterviewSession(
            id=interview_id,
            user_id=user_id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hash",
            full_name="John Doe",
        )

        mock_session = AsyncMock()

        call_count = 0
        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()

            if call_count == 1:  # Share query
                result.first.return_value = share
            elif call_count == 2:  # Interview query
                result.first.return_value = interview
            elif call_count == 3:  # User query
                result.first.return_value = user
            elif call_count == 4:  # Session feedback query
                result.first.return_value = None
            elif call_count == 5:  # Responses query
                result.all.return_value = []
            else:
                result.first.return_value = None

            return result

        mock_session.exec = mock_exec

        result = await service.get_shared_interview(mock_session, "valid_token")

        assert share.view_count == 6  # Incremented
        assert result.shared_by == "John"  # First name only
        mock_session.commit.assert_called()


class TestShareServiceRevokeLink:
    """Tests for revoking share links."""

    @pytest.mark.asyncio
    async def test_revoke_share_link_not_found(self):
        """Should raise ValueError if share doesn't exist."""
        service = ShareService()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Share .* not found"):
            await service.revoke_share_link(mock_session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_revoke_share_link_access_denied(self):
        """Should raise ValueError if user doesn't own share."""
        service = ShareService()

        share = InterviewShare(
            id=uuid4(),
            interview_id=uuid4(),
            created_by=uuid4(),  # Different user
            token="token",
            expires_at=datetime.now(UTC) + timedelta(days=3),
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = share
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="access denied"):
            await service.revoke_share_link(mock_session, share.id, uuid4())

    @pytest.mark.asyncio
    async def test_revoke_share_link_success(self):
        """Should delete share on successful revoke."""
        service = ShareService()
        user_id = uuid4()

        share = InterviewShare(
            id=uuid4(),
            interview_id=uuid4(),
            created_by=user_id,
            token="token",
            expires_at=datetime.now(UTC) + timedelta(days=3),
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = share
        mock_session.exec.return_value = mock_result

        result = await service.revoke_share_link(mock_session, share.id, user_id)

        assert result is True
        mock_session.delete.assert_called_once_with(share)
        mock_session.commit.assert_called_once()


class TestShareServiceGetSharesForInterview:
    """Tests for listing shares for an interview."""

    @pytest.mark.asyncio
    async def test_get_shares_returns_empty_for_unauthorized(self):
        """Should return empty list if user doesn't own interview."""
        service = ShareService()

        interview = InterviewSession(
            id=uuid4(),
            user_id=uuid4(),  # Different user
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = interview
        mock_session.exec.return_value = mock_result

        result = await service.get_shares_for_interview(mock_session, interview.id, uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_get_shares_returns_list(self):
        """Should return list of shares for owned interview."""
        service = ShareService()
        user_id = uuid4()
        interview_id = uuid4()

        interview = InterviewSession(
            id=interview_id,
            user_id=user_id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.COMPLETED,
        )

        shares = [
            InterviewShare(
                id=uuid4(),
                interview_id=interview_id,
                created_by=user_id,
                token="token1",
                expires_at=datetime.now(UTC) + timedelta(days=3),
            ),
            InterviewShare(
                id=uuid4(),
                interview_id=interview_id,
                created_by=user_id,
                token="token2",
                expires_at=datetime.now(UTC) + timedelta(days=5),
            ),
        ]

        mock_session = AsyncMock()

        call_count = 0
        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()

            if call_count == 1:  # Interview query
                result.first.return_value = interview
            elif call_count == 2:  # Shares query
                result.all.return_value = shares

            return result

        mock_session.exec = mock_exec

        result = await service.get_shares_for_interview(mock_session, interview_id, user_id)

        assert len(result) == 2
        assert result[0].token == "token1"
        assert result[1].token == "token2"


class TestInterviewShareModel:
    """Tests for InterviewShare model."""

    def test_is_expired_false_when_future(self):
        """Share should not be expired when expires_at is in the future."""
        share = InterviewShare(
            id=uuid4(),
            interview_id=uuid4(),
            created_by=uuid4(),
            token="token",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        assert share.is_expired is False

    def test_is_expired_true_when_past(self):
        """Share should be expired when expires_at is in the past."""
        share = InterviewShare(
            id=uuid4(),
            interview_id=uuid4(),
            created_by=uuid4(),
            token="token",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        assert share.is_expired is True
