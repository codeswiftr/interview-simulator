"""Pure unit tests for ShareService.

Tests all methods with mocked AsyncSession. No database required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from uuid import uuid4

import pytest

from app.services.share_service import ShareService


@pytest.fixture
def service():
    return ShareService()


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def interview_id():
    return uuid4()


class TestCreateShareLink:
    @pytest.mark.asyncio
    async def test_creates_new_share(self, service, mock_session, user_id, interview_id):
        interview = MagicMock()
        interview.user_id = user_id

        interview_result = MagicMock()
        interview_result.first.return_value = interview

        existing_result = MagicMock()
        existing_result.first.return_value = None

        mock_session.exec.side_effect = [interview_result, existing_result]

        share = await service.create_share_link(mock_session, interview_id, user_id)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_existing_active_share(self, service, mock_session, user_id, interview_id):
        interview = MagicMock()
        interview.user_id = user_id

        existing_share = MagicMock()

        interview_result = MagicMock()
        interview_result.first.return_value = interview

        existing_result = MagicMock()
        existing_result.first.return_value = existing_share

        mock_session.exec.side_effect = [interview_result, existing_result]

        result = await service.create_share_link(mock_session, interview_id, user_id)
        assert result is existing_share
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_if_interview_not_found(self, service, mock_session, user_id, interview_id):
        interview_result = MagicMock()
        interview_result.first.return_value = None
        mock_session.exec.return_value = interview_result

        with pytest.raises(ValueError, match="not found"):
            await service.create_share_link(mock_session, interview_id, user_id)

    @pytest.mark.asyncio
    async def test_raises_if_not_owner(self, service, mock_session, interview_id):
        interview = MagicMock()
        interview.user_id = uuid4()

        interview_result = MagicMock()
        interview_result.first.return_value = interview
        mock_session.exec.return_value = interview_result

        with pytest.raises(ValueError, match="access denied"):
            await service.create_share_link(mock_session, interview_id, uuid4())


class TestGetSharedInterview:
    @pytest.mark.asyncio
    async def test_raises_if_token_not_found(self, service, mock_session):
        share_result = MagicMock()
        share_result.first.return_value = None
        mock_session.exec.return_value = share_result

        with pytest.raises(ValueError, match="not found"):
            await service.get_shared_interview(mock_session, "bad-token")

    @pytest.mark.asyncio
    async def test_raises_if_expired(self, service, mock_session):
        share = MagicMock()
        share.is_expired = True

        share_result = MagicMock()
        share_result.first.return_value = share
        mock_session.exec.return_value = share_result

        with pytest.raises(ValueError, match="expired"):
            await service.get_shared_interview(mock_session, "expired-token")

    @pytest.mark.asyncio
    async def test_increments_view_count(self, service, mock_session):
        share = MagicMock()
        share.is_expired = False
        share.view_count = 5
        share.interview_id = uuid4()
        share.created_by = uuid4()

        interview = MagicMock()
        interview.id = share.interview_id
        interview.interview_type = MagicMock()
        interview.interview_type.value = "behavioral"
        interview.created_at = datetime.now(UTC)

        user = MagicMock()
        user.full_name = "John Doe"

        session_feedback = MagicMock()
        session_feedback.overall_score = 8.0
        session_feedback.audio_score = 7.0
        session_feedback.content_score = 9.0

        share_result = MagicMock()
        share_result.first.return_value = share
        interview_result = MagicMock()
        interview_result.first.return_value = interview
        user_result = MagicMock()
        user_result.first.return_value = user
        feedback_result = MagicMock()
        feedback_result.first.return_value = session_feedback
        responses_result = MagicMock()
        responses_result.all.return_value = []

        mock_session.exec.side_effect = [
            share_result, interview_result, user_result,
            feedback_result, responses_result,
        ]

        result = await service.get_shared_interview(mock_session, "valid-token")
        assert share.view_count == 6
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_raises_if_interview_not_found(self, service, mock_session):
        share = MagicMock()
        share.is_expired = False
        share.view_count = 0
        share.interview_id = uuid4()

        share_result = MagicMock()
        share_result.first.return_value = share
        interview_result = MagicMock()
        interview_result.first.return_value = None

        mock_session.exec.side_effect = [share_result, interview_result]

        with pytest.raises(ValueError, match="Interview not found"):
            await service.get_shared_interview(mock_session, "token")

    @pytest.mark.asyncio
    async def test_shared_by_full_name(self, service, mock_session):
        share = MagicMock()
        share.is_expired = False
        share.view_count = 0
        share.interview_id = uuid4()
        share.created_by = uuid4()

        interview = MagicMock()
        interview.id = share.interview_id
        interview.interview_type = MagicMock()
        interview.interview_type.value = "technical"
        interview.created_at = datetime.now(UTC)

        user = MagicMock()
        user.full_name = "Jane Smith"

        share_result = MagicMock()
        share_result.first.return_value = share
        interview_result = MagicMock()
        interview_result.first.return_value = interview
        user_result = MagicMock()
        user_result.first.return_value = user
        feedback_result = MagicMock()
        feedback_result.first.return_value = None
        responses_result = MagicMock()
        responses_result.all.return_value = []

        mock_session.exec.side_effect = [
            share_result, interview_result, user_result,
            feedback_result, responses_result,
        ]

        result = await service.get_shared_interview(mock_session, "token")
        assert result.shared_by == "Jane"

    @pytest.mark.asyncio
    async def test_shared_by_email_prefix_no_name(self, service, mock_session):
        share = MagicMock()
        share.is_expired = False
        share.view_count = 0
        share.interview_id = uuid4()
        share.created_by = uuid4()

        interview = MagicMock()
        interview.id = share.interview_id
        interview.interview_type = MagicMock()
        interview.interview_type.value = "behavioral"
        interview.created_at = datetime.now(UTC)

        user = MagicMock()
        user.full_name = None
        user.email = "jdoe@example.com"

        share_result = MagicMock()
        share_result.first.return_value = share
        interview_result = MagicMock()
        interview_result.first.return_value = interview
        user_result = MagicMock()
        user_result.first.return_value = user
        feedback_result = MagicMock()
        feedback_result.first.return_value = None
        responses_result = MagicMock()
        responses_result.all.return_value = []

        mock_session.exec.side_effect = [
            share_result, interview_result, user_result,
            feedback_result, responses_result,
        ]

        result = await service.get_shared_interview(mock_session, "token")
        assert result.shared_by == "jdoe"

    @pytest.mark.asyncio
    async def test_shared_by_fallback_no_user(self, service, mock_session):
        share = MagicMock()
        share.is_expired = False
        share.view_count = 0
        share.interview_id = uuid4()
        share.created_by = uuid4()

        interview = MagicMock()
        interview.id = share.interview_id
        interview.interview_type = MagicMock()
        interview.interview_type.value = "behavioral"
        interview.created_at = datetime.now(UTC)

        share_result = MagicMock()
        share_result.first.return_value = share
        interview_result = MagicMock()
        interview_result.first.return_value = interview
        user_result = MagicMock()
        user_result.first.return_value = None
        feedback_result = MagicMock()
        feedback_result.first.return_value = None
        responses_result = MagicMock()
        responses_result.all.return_value = []

        mock_session.exec.side_effect = [
            share_result, interview_result, user_result,
            feedback_result, responses_result,
        ]

        result = await service.get_shared_interview(mock_session, "token")
        assert result.shared_by == "A user"

    @pytest.mark.asyncio
    async def test_with_responses_and_feedback(self, service, mock_session):
        share = MagicMock()
        share.is_expired = False
        share.view_count = 0
        share.interview_id = uuid4()
        share.created_by = uuid4()

        interview = MagicMock()
        interview.id = share.interview_id
        interview.interview_type = MagicMock()
        interview.interview_type.value = "behavioral"
        interview.created_at = datetime.now(UTC)

        user = MagicMock()
        user.full_name = "Test User"

        response = MagicMock()
        response.question_id = uuid4()
        response.id = uuid4()
        response.transcript = "My answer"
        response.duration_seconds = 120

        question = MagicMock()
        question.content = "Tell me about a challenge"
        question.category = MagicMock()
        question.category.value = "behavioral"
        question.difficulty = MagicMock()
        question.difficulty.value = "medium"

        content_fb = MagicMock()
        content_fb.overall_content_score = 8
        content_fb.strengths = ["good", "great", "excellent", "superb"]
        content_fb.improvements = ["more detail", "structure", "examples", "pace"]

        share_result = MagicMock()
        share_result.first.return_value = share
        interview_result = MagicMock()
        interview_result.first.return_value = interview
        user_result = MagicMock()
        user_result.first.return_value = user
        session_fb_result = MagicMock()
        session_fb_result.first.return_value = None
        responses_result = MagicMock()
        responses_result.all.return_value = [response]
        question_result = MagicMock()
        question_result.first.return_value = question
        content_fb_result = MagicMock()
        content_fb_result.first.return_value = content_fb

        mock_session.exec.side_effect = [
            share_result, interview_result, user_result,
            session_fb_result, responses_result,
            question_result, content_fb_result,
        ]

        result = await service.get_shared_interview(mock_session, "token")
        assert result.question_count == 1
        assert len(result.responses) == 1
        resp_data = result.responses[0]
        assert resp_data["question"] == "Tell me about a challenge"
        assert resp_data["score"] == 8
        assert len(resp_data["strengths"]) == 3
        assert len(resp_data["improvements"]) == 3


class TestRevokeShareLink:
    @pytest.mark.asyncio
    async def test_revokes_successfully(self, service, mock_session):
        share_id = uuid4()
        user_id = uuid4()
        share = MagicMock()
        share.created_by = user_id

        share_result = MagicMock()
        share_result.first.return_value = share
        mock_session.exec.return_value = share_result

        result = await service.revoke_share_link(mock_session, share_id, user_id)
        assert result is True
        mock_session.delete.assert_awaited_once_with(share)
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_if_not_found(self, service, mock_session):
        share_result = MagicMock()
        share_result.first.return_value = None
        mock_session.exec.return_value = share_result

        with pytest.raises(ValueError, match="not found"):
            await service.revoke_share_link(mock_session, uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_not_owner(self, service, mock_session):
        share = MagicMock()
        share.created_by = uuid4()

        share_result = MagicMock()
        share_result.first.return_value = share
        mock_session.exec.return_value = share_result

        with pytest.raises(ValueError, match="access denied"):
            await service.revoke_share_link(mock_session, uuid4(), uuid4())


class TestGetSharesForInterview:
    @pytest.mark.asyncio
    async def test_returns_shares(self, service, mock_session, user_id, interview_id):
        interview = MagicMock()
        interview.user_id = user_id

        shares = [MagicMock(), MagicMock()]

        interview_result = MagicMock()
        interview_result.first.return_value = interview
        shares_result = MagicMock()
        shares_result.all.return_value = shares

        mock_session.exec.side_effect = [interview_result, shares_result]

        result = await service.get_shares_for_interview(mock_session, interview_id, user_id)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_if_not_owner(self, service, mock_session, interview_id):
        interview = MagicMock()
        interview.user_id = uuid4()

        interview_result = MagicMock()
        interview_result.first.return_value = interview
        mock_session.exec.return_value = interview_result

        result = await service.get_shares_for_interview(mock_session, interview_id, uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_if_interview_not_found(self, service, mock_session, interview_id):
        interview_result = MagicMock()
        interview_result.first.return_value = None
        mock_session.exec.return_value = interview_result

        result = await service.get_shares_for_interview(mock_session, interview_id, uuid4())
        assert result == []
