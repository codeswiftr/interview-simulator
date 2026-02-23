"""Unit tests for main FeedbackService methods without database.

Focuses on generate_feedback, generate_session_feedback, and getter methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.feedback import ContentFeedback, SessionFeedback, VideoFeedback
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    ProcessingStatus,
)
from app.models.question import Question
from app.models.user import User
from app.services.feedback_service import FeedbackService


@pytest.fixture
def feedback_service():
    """Provide FeedbackService instance."""
    return FeedbackService()


class TestFeedbackServiceInit:
    """Tests for FeedbackService initialization."""

    def test_initializes_content_analyzer(self):
        """Test that content_analyzer is initialized."""
        service = FeedbackService()
        assert service.content_analyzer is not None

    def test_initializes_video_service(self):
        """Test that video_service is initialized."""
        service = FeedbackService()
        assert service.video_service is not None


class TestGenerateFeedback:
    """Tests for generate_feedback method."""

    @pytest.mark.asyncio
    async def test_raises_if_response_not_found(self, feedback_service):
        """Test raises ValueError if response not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="not found"):
            await feedback_service.generate_feedback(mock_session, uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_feedback_already_exists(self, feedback_service):
        """Test raises ValueError if feedback already exists."""
        response_id = uuid4()
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id

        mock_existing_feedback = MagicMock(spec=ContentFeedback)

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_response
            else:
                mock_result.first.return_value = mock_existing_feedback
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        with pytest.raises(ValueError, match="already exists"):
            await feedback_service.generate_feedback(mock_session, response_id)

    @pytest.mark.asyncio
    async def test_raises_if_no_transcript(self, feedback_service):
        """Test raises ValueError if response has no transcript."""
        response_id = uuid4()
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_response.transcript = None  # No transcript

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_response
            else:
                mock_result.first.return_value = None  # No existing feedback
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        with pytest.raises(ValueError, match="no transcript"):
            await feedback_service.generate_feedback(mock_session, response_id)

    @pytest.mark.asyncio
    async def test_raises_if_question_not_found(self, feedback_service):
        """Test raises ValueError if question not found."""
        response_id = uuid4()
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_response.transcript = "Test transcript"
        mock_response.question_id = uuid4()

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_response
            elif call_count == 2:
                mock_result.first.return_value = None  # No existing feedback
            else:
                mock_result.first.return_value = None  # Question not found
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        with pytest.raises(ValueError, match="Question.*not found"):
            await feedback_service.generate_feedback(mock_session, response_id)

    @pytest.mark.asyncio
    async def test_generates_feedback_successfully(self, feedback_service):
        """Test successful feedback generation."""
        response_id = uuid4()
        session_id = uuid4()
        question_id = uuid4()
        user_id = uuid4()

        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_response.transcript = "This is my test answer"
        mock_response.question_id = question_id
        mock_response.session_id = session_id

        mock_question = MagicMock(spec=Question)
        mock_question.id = question_id
        mock_question.content = "Tell me about yourself"
        mock_question.category = "behavioral"

        mock_interview = MagicMock(spec=InterviewSession)
        mock_interview.id = session_id
        mock_interview.user_id = user_id

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.experience_level = "senior"

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_response
            elif call_count == 2:
                mock_result.first.return_value = None  # No existing feedback
            elif call_count == 3:
                mock_result.first.return_value = mock_question
            elif call_count == 4:
                mock_result.first.return_value = mock_interview
            else:
                mock_result.first.return_value = mock_user
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_metrics = MagicMock()
        mock_metrics.technical_accuracy = 75
        mock_metrics.star_adherence = 80
        mock_metrics.answer_structure = 85
        mock_metrics.completeness = 78
        mock_metrics.relevance = 82
        mock_metrics.strengths = ["Good structure"]
        mock_metrics.improvements = ["Add more examples"]
        mock_metrics.detailed_feedback = "Detailed analysis..."

        with (
            patch.object(
                feedback_service.content_analyzer,
                "analyze",
                new_callable=AsyncMock,
                return_value=mock_metrics,
            ),
            patch.object(
                feedback_service.content_analyzer, "calculate_overall_score", return_value=80.0
            ),
        ):
            result = await feedback_service.generate_feedback(mock_session, response_id)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestGenerateSessionFeedback:
    """Tests for generate_session_feedback method."""

    @pytest.mark.asyncio
    async def test_raises_if_session_not_found(self, feedback_service):
        """Test raises ValueError if session not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="not found"):
            await feedback_service.generate_session_feedback(mock_session, uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_session_feedback_already_exists(self, feedback_service):
        """Test raises ValueError if session feedback already exists."""
        session_id = uuid4()
        mock_interview = MagicMock(spec=InterviewSession)
        mock_interview.id = session_id

        mock_existing_feedback = MagicMock(spec=SessionFeedback)

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_interview
            else:
                mock_result.first.return_value = mock_existing_feedback
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        with pytest.raises(ValueError, match="already exists"):
            await feedback_service.generate_session_feedback(mock_session, session_id)

    @pytest.mark.asyncio
    async def test_raises_if_no_responses(self, feedback_service):
        """Test raises ValueError if no responses found."""
        session_id = uuid4()
        mock_interview = MagicMock(spec=InterviewSession)
        mock_interview.id = session_id

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_interview
            elif call_count == 2:
                mock_result.first.return_value = None  # No existing session feedback
            else:
                mock_result.all.return_value = []  # No responses
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        with pytest.raises(ValueError, match="No responses found"):
            await feedback_service.generate_session_feedback(mock_session, session_id)


class TestGetResponseFeedback:
    """Tests for get_response_feedback method."""

    @pytest.mark.asyncio
    async def test_returns_feedback_when_exists(self, feedback_service):
        """Test returns ContentFeedback when it exists."""
        response_id = uuid4()
        mock_feedback = MagicMock(spec=ContentFeedback)
        mock_feedback.response_id = response_id

        mock_result = MagicMock()
        mock_result.first.return_value = mock_feedback

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_response_feedback(mock_session, response_id)

        assert result == mock_feedback

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, feedback_service):
        """Test returns None when feedback doesn't exist."""
        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_response_feedback(mock_session, uuid4())

        assert result is None


class TestGetVideoFeedback:
    """Tests for get_video_feedback method."""

    @pytest.mark.asyncio
    async def test_returns_feedback_when_exists(self, feedback_service):
        """Test returns VideoFeedback when it exists."""
        response_id = uuid4()
        mock_feedback = MagicMock(spec=VideoFeedback)
        mock_feedback.response_id = response_id

        mock_result = MagicMock()
        mock_result.first.return_value = mock_feedback

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_video_feedback(mock_session, response_id)

        assert result == mock_feedback

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, feedback_service):
        """Test returns None when video feedback doesn't exist."""
        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_video_feedback(mock_session, uuid4())

        assert result is None


class TestGenerateVideoFeedback:
    """Tests for generate_video_feedback method."""

    @pytest.mark.asyncio
    async def test_raises_if_response_not_found(self, feedback_service):
        """Test raises ValueError if response not found."""
        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="not found"):
            await feedback_service.generate_video_feedback(mock_session, uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_no_video_url(self, feedback_service):
        """Test raises ValueError if response has no video_url."""
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.video_url = None

        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="no video attached"):
            await feedback_service.generate_video_feedback(mock_session, uuid4())

    @pytest.mark.asyncio
    async def test_raises_if_video_feedback_already_exists(self, feedback_service):
        """Test raises ValueError if video feedback already exists."""
        response_id = uuid4()
        mock_response = MagicMock(spec=InterviewResponse)
        mock_response.id = response_id
        mock_response.video_url = "/uploads/video/test.mp4"

        mock_existing = MagicMock(spec=VideoFeedback)

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = mock_response
            else:
                mock_result.first.return_value = mock_existing
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        with pytest.raises(ValueError, match="already exists"):
            await feedback_service.generate_video_feedback(mock_session, response_id)


class TestGetSessionFeedback:
    """Tests for get_session_feedback method."""

    @pytest.mark.asyncio
    async def test_returns_feedback_when_exists(self, feedback_service):
        """Test returns SessionFeedback when it exists."""
        session_id = uuid4()
        mock_feedback = MagicMock(spec=SessionFeedback)
        mock_feedback.session_id = session_id

        mock_result = MagicMock()
        mock_result.first.return_value = mock_feedback

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_session_feedback(mock_session, session_id)

        assert result == mock_feedback

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, feedback_service):
        """Test returns None when session feedback doesn't exist."""
        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_session_feedback(mock_session, uuid4())

        assert result is None


class TestGetAllSessionFeedbacks:
    """Tests for get_all_session_feedbacks method."""

    @pytest.mark.asyncio
    async def test_returns_list_of_feedbacks(self, feedback_service):
        """Test returns list of ContentFeedback for session."""
        session_id = uuid4()
        mock_feedbacks = [
            MagicMock(spec=ContentFeedback),
            MagicMock(spec=ContentFeedback),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_feedbacks

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_all_session_feedbacks(mock_session, session_id)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none(self, feedback_service):
        """Test returns empty list when no feedbacks exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_all_session_feedbacks(mock_session, uuid4())

        assert result == []


class TestGetProcessingSummary:
    """Tests for get_processing_summary method."""

    @pytest.mark.asyncio
    async def test_returns_correct_status_counts(self, feedback_service):
        """Test returns correct processing status counts."""
        session_id = uuid4()

        mock_responses = [
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.COMPLETED),
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.COMPLETED),
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.PENDING),
        ]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_responses
            else:
                mock_result.first.return_value = None  # No session feedback
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_processing_summary(mock_session, session_id)

        assert result["status_counts"]["completed"] == 2
        assert result["status_counts"]["pending"] == 1
        assert result["total_responses"] == 3
        assert result["has_session_feedback"] is False
        assert result["all_processed"] is False

    @pytest.mark.asyncio
    async def test_identifies_transcribing_step(self, feedback_service):
        """Test identifies transcribing as current step."""
        session_id = uuid4()

        mock_responses = [
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.TRANSCRIBING),
        ]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_responses
            else:
                mock_result.first.return_value = None
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_processing_summary(mock_session, session_id)

        assert result["current_step"] == "transcribing"

    @pytest.mark.asyncio
    async def test_identifies_analyzing_step(self, feedback_service):
        """Test identifies analyzing as current step."""
        session_id = uuid4()

        mock_responses = [
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.ANALYZING),
        ]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_responses
            else:
                mock_result.first.return_value = None
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_processing_summary(mock_session, session_id)

        assert result["current_step"] == "analyzing"

    @pytest.mark.asyncio
    async def test_identifies_complete_step(self, feedback_service):
        """Test identifies complete when session feedback exists."""
        session_id = uuid4()

        mock_responses = [
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.COMPLETED),
        ]

        mock_session_feedback = MagicMock(spec=SessionFeedback)

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_responses
            else:
                mock_result.first.return_value = mock_session_feedback
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_processing_summary(mock_session, session_id)

        assert result["current_step"] == "complete"
        assert result["has_session_feedback"] is True

    @pytest.mark.asyncio
    async def test_identifies_generating_feedback_step(self, feedback_service):
        """Test identifies generating_feedback when completed but no session feedback."""
        session_id = uuid4()

        mock_responses = [
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.COMPLETED),
        ]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_responses
            else:
                mock_result.first.return_value = None  # No session feedback
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_processing_summary(mock_session, session_id)

        assert result["current_step"] == "generating_feedback"

    @pytest.mark.asyncio
    async def test_identifies_failed_step(self, feedback_service):
        """Test identifies failed when all responses failed."""
        session_id = uuid4()

        mock_responses = [
            MagicMock(spec=InterviewResponse, processing_status=ProcessingStatus.FAILED),
        ]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_responses
            else:
                mock_result.first.return_value = None
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_processing_summary(mock_session, session_id)

        assert result["current_step"] == "failed"


class TestGetUserProgress:
    """Tests for get_user_progress method."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_sessions(self, feedback_service):
        """Test returns empty progress when no sessions exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_user_progress(mock_session, uuid4())

        assert result["recommended_practice_areas"] == []
        assert result["average_audio_score"] is None
        assert result["average_content_score"] is None

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_feedbacks(self, feedback_service):
        """Test returns empty progress when sessions exist but no feedbacks."""
        mock_sessions = [MagicMock(spec=InterviewSession, id=uuid4())]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_sessions
            else:
                mock_result.all.return_value = []  # No feedbacks
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_user_progress(mock_session, uuid4())

        assert result["recommended_practice_areas"] == []
        assert result["average_audio_score"] is None
        assert result["average_content_score"] is None

    @pytest.mark.asyncio
    async def test_calculates_averages_correctly(self, feedback_service):
        """Test calculates average scores correctly."""
        session_id_1 = uuid4()
        session_id_2 = uuid4()

        mock_sessions = [
            MagicMock(spec=InterviewSession, id=session_id_1),
            MagicMock(spec=InterviewSession, id=session_id_2),
        ]

        mock_feedbacks = [
            MagicMock(
                spec=SessionFeedback,
                session_id=session_id_1,
                audio_score=80.0,
                content_score=85.0,
                recommended_practice_areas=["STAR method"],
            ),
            MagicMock(
                spec=SessionFeedback,
                session_id=session_id_2,
                audio_score=70.0,
                content_score=75.0,
                recommended_practice_areas=["Technical depth", "STAR method"],
            ),
        ]

        call_count = 0

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.all.return_value = mock_sessions
            else:
                mock_result.all.return_value = mock_feedbacks
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)

        result = await feedback_service.get_user_progress(mock_session, uuid4())

        # Average audio: (80 + 70) / 2 = 75
        assert result["average_audio_score"] == 75.0
        # Average content: (85 + 75) / 2 = 80
        assert result["average_content_score"] == 80.0
        # STAR method appears twice, should be first
        assert "STAR method" in result["recommended_practice_areas"]
