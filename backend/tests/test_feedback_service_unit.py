"""Pure unit tests for FeedbackService methods without database.

These tests mock database interactions to test the computation logic directly,
allowing test execution without a running PostgreSQL instance.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.feedback import AudioFeedback, ContentFeedback
from app.models.interview import InterviewResponse, InterviewSession
from app.models.question import Question
from app.services.feedback_service import FeedbackService


@pytest.fixture
def feedback_service():
    """Provide FeedbackService instance."""
    return FeedbackService()


class TestGetTrendUnit:
    """Unit tests for _get_trend helper."""

    def test_improving_trend(self, feedback_service):
        assert feedback_service._get_trend(85, 80) == "improving"

    def test_declining_trend(self, feedback_service):
        assert feedback_service._get_trend(75, 80) == "declining"

    def test_stable_trend(self, feedback_service):
        assert feedback_service._get_trend(81, 80) == "stable"

    def test_stable_at_exact_boundary(self, feedback_service):
        assert feedback_service._get_trend(82, 80) == "stable"

    def test_improving_just_over_boundary(self, feedback_service):
        assert feedback_service._get_trend(82.01, 80) == "improving"


class TestAggregateDelivery:
    """Unit tests for _aggregate_delivery helper."""

    def _create_mock_response(self, session_id: str, question_category: str = "behavioral"):
        """Create a mock response with question."""
        response = MagicMock(spec=InterviewResponse)
        response.id = uuid4()
        response.session_id = session_id

        question = MagicMock(spec=Question)
        question.category = question_category

        return (response, question)

    def _create_mock_audio_feedback(
        self,
        response_id,
        speech_rate_score=75,
        filler_word_score=70,
        confidence_score=80,
        volume_consistency=78,
        speech_rate_wpm=140,
        filler_words=None,
    ):
        """Create a mock AudioFeedback."""
        af = MagicMock(spec=AudioFeedback)
        af.response_id = response_id
        af.speech_rate_score = speech_rate_score
        af.filler_word_score = filler_word_score
        af.confidence_score = confidence_score
        af.volume_consistency = volume_consistency
        af.speech_rate_wpm = speech_rate_wpm
        af.filler_words = filler_words or {}
        return af

    def test_returns_none_when_no_recent_scores(self, feedback_service):
        """Test returns None when no audio feedback for recent sessions."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        previous_session = MagicMock(spec=InterviewSession)
        previous_session.id = uuid4()

        # Responses without audio feedback
        responses = [
            self._create_mock_response(str(recent_session.id)),
            self._create_mock_response(str(previous_session.id)),
        ]

        result = feedback_service._aggregate_delivery(
            responses,
            {},  # Empty audio feedbacks
            [recent_session],
            [previous_session],
        )

        assert result is None

    def test_returns_delivery_metrics_when_audio_feedback_exists(self, feedback_service):
        """Test returns delivery metrics when audio feedback exists."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        previous_session = MagicMock(spec=InterviewSession)
        previous_session.id = uuid4()

        # Create responses
        resp1, q1 = self._create_mock_response(recent_session.id)
        resp2, q2 = self._create_mock_response(previous_session.id)

        # Create audio feedbacks
        audio_feedbacks = {
            resp1.id: self._create_mock_audio_feedback(
                resp1.id, speech_rate_score=85, filler_word_score=90, confidence_score=88, volume_consistency=85
            ),
            resp2.id: self._create_mock_audio_feedback(
                resp2.id, speech_rate_score=70, filler_word_score=65, confidence_score=72, volume_consistency=70
            ),
        }

        result = feedback_service._aggregate_delivery(
            [(resp1, q1), (resp2, q2)],
            audio_feedbacks,
            [recent_session],
            [previous_session],
        )

        assert result is not None
        assert "current_score" in result
        assert "previous_score" in result
        assert "trend" in result
        assert result["trend"] in ["improving", "declining", "stable"]

    def test_captures_low_filler_word_improvement(self, feedback_service):
        """Test captures low filler word usage as improvement."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id)

        audio_feedbacks = {
            resp.id: self._create_mock_audio_feedback(
                resp.id, filler_word_score=85  # High score = low fillers
            ),
        }

        result = feedback_service._aggregate_delivery(
            [(resp, q)],
            audio_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert "Low filler word usage" in result["improvements"]

    def test_captures_high_filler_word_area(self, feedback_service):
        """Test captures high filler word count as area to work on."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id)

        audio_feedbacks = {
            resp.id: self._create_mock_audio_feedback(
                resp.id,
                filler_word_score=45,  # Low score = many fillers
                filler_words={"um": 10, "uh": 8},
            ),
        }

        result = feedback_service._aggregate_delivery(
            [(resp, q)],
            audio_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert any("filler words" in area.lower() for area in result["areas_to_work_on"])

    def test_captures_fast_speech_area(self, feedback_service):
        """Test captures fast speech as area to work on."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id)

        audio_feedbacks = {
            resp.id: self._create_mock_audio_feedback(
                resp.id,
                speech_rate_score=50,
                speech_rate_wpm=180,  # Too fast
            ),
        }

        result = feedback_service._aggregate_delivery(
            [(resp, q)],
            audio_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert any("slow down" in area.lower() for area in result["areas_to_work_on"])

    def test_captures_slow_speech_area(self, feedback_service):
        """Test captures slow speech as area to work on."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id)

        audio_feedbacks = {
            resp.id: self._create_mock_audio_feedback(
                resp.id,
                speech_rate_score=50,
                speech_rate_wpm=95,  # Too slow
            ),
        }

        result = feedback_service._aggregate_delivery(
            [(resp, q)],
            audio_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert any("speed up" in area.lower() for area in result["areas_to_work_on"])


class TestAggregateBehavioral:
    """Unit tests for _aggregate_behavioral helper."""

    def _create_mock_response(self, session_id: str, question_category: str):
        """Create a mock response with question."""
        response = MagicMock(spec=InterviewResponse)
        response.id = uuid4()
        response.session_id = session_id

        question = MagicMock(spec=Question)
        question.category = question_category

        return (response, question)

    def _create_mock_content_feedback(
        self,
        response_id,
        star_adherence=75,
        answer_structure=70,
        completeness=72,
        strengths=None,
        improvements=None,
    ):
        """Create a mock ContentFeedback."""
        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = response_id
        cf.star_adherence = star_adherence
        cf.answer_structure = answer_structure
        cf.completeness = completeness
        cf.strengths = strengths or []
        cf.improvements = improvements or []
        return cf

    def test_returns_none_for_non_behavioral_questions(self, feedback_service):
        """Test returns None when no behavioral questions."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        # Technical question, not behavioral
        resp, q = self._create_mock_response(session.id, "technical")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(resp.id),
        }

        result = feedback_service._aggregate_behavioral(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is None

    def test_returns_metrics_for_behavioral_questions(self, feedback_service):
        """Test returns metrics for behavioral questions."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id, "behavioral")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(
                resp.id, star_adherence=85, answer_structure=80, completeness=78
            ),
        }

        result = feedback_service._aggregate_behavioral(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert "current_score" in result
        # Score = 0.4 * 85 + 0.35 * 80 + 0.25 * 78 = 34 + 28 + 19.5 = 81.5
        assert result["current_score"] == 81.5

    def test_captures_star_improvements(self, feedback_service):
        """Test captures STAR method improvements."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id, "behavioral")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(
                resp.id,
                star_adherence=85,  # High STAR score
                strengths=["Great STAR method usage"],
            ),
        }

        result = feedback_service._aggregate_behavioral(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert any("STAR" in s for s in result["improvements"])

    def test_captures_low_star_area(self, feedback_service):
        """Test captures low STAR adherence as area to work on."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id, "behavioral")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(
                resp.id, star_adherence=50  # Low STAR score
            ),
        }

        result = feedback_service._aggregate_behavioral(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert any("STAR" in area for area in result["areas_to_work_on"])


class TestAggregateTechnical:
    """Unit tests for _aggregate_technical helper."""

    def _create_mock_response(self, session_id: str, question_category: str):
        """Create a mock response with question."""
        response = MagicMock(spec=InterviewResponse)
        response.id = uuid4()
        response.session_id = session_id

        question = MagicMock(spec=Question)
        question.category = question_category

        return (response, question)

    def _create_mock_content_feedback(
        self,
        response_id,
        technical_accuracy=75,
        completeness=70,
        relevance=72,
        strengths=None,
        improvements=None,
    ):
        """Create a mock ContentFeedback."""
        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = response_id
        cf.technical_accuracy = technical_accuracy
        cf.completeness = completeness
        cf.relevance = relevance
        cf.strengths = strengths or []
        cf.improvements = improvements or []
        return cf

    def test_returns_none_for_non_technical_questions(self, feedback_service):
        """Test returns None when no technical questions."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        # Behavioral question, not technical
        resp, q = self._create_mock_response(session.id, "behavioral")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(resp.id),
        }

        result = feedback_service._aggregate_technical(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is None

    def test_returns_metrics_for_technical_questions(self, feedback_service):
        """Test returns metrics for technical questions."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id, "technical")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(
                resp.id, technical_accuracy=85, completeness=80, relevance=78
            ),
        }

        result = feedback_service._aggregate_technical(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert "current_score" in result
        # Score = 0.4 * 85 + 0.35 * 80 + 0.25 * 78 = 34 + 28 + 19.5 = 81.5
        assert result["current_score"] == 81.5

    def test_returns_metrics_for_system_design_questions(self, feedback_service):
        """Test returns metrics for system_design questions."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id, "system_design")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(
                resp.id, technical_accuracy=80, completeness=75, relevance=85
            ),
        }

        result = feedback_service._aggregate_technical(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert "current_score" in result

    def test_captures_technical_improvements(self, feedback_service):
        """Test captures technical accuracy improvements."""
        session = MagicMock(spec=InterviewSession)
        session.id = uuid4()

        resp, q = self._create_mock_response(session.id, "technical")

        content_feedbacks = {
            resp.id: self._create_mock_content_feedback(
                resp.id,
                technical_accuracy=85,  # High technical score
                strengths=["Key terminology used correctly"],
            ),
        }

        result = feedback_service._aggregate_technical(
            [(resp, q)],
            content_feedbacks,
            [session],
            [],
        )

        assert result is not None
        assert any("terminology" in s.lower() for s in result["improvements"])


class TestComputeDimensionHelpers:
    """Unit tests for _compute_*_dimension helpers."""

    def _create_mock_response(self, session_id: str, question_category: str):
        """Create a mock response with question."""
        response = MagicMock(spec=InterviewResponse)
        response.id = uuid4()
        response.session_id = session_id

        question = MagicMock(spec=Question)
        question.category = question_category

        return (response, question)

    def test_compute_content_dimension(self, feedback_service):
        """Test _compute_content_dimension calculation."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        resp, q = self._create_mock_response(recent_session.id, "behavioral")

        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = resp.id
        cf.overall_content_score = 82.5

        result = feedback_service._compute_content_dimension(
            [(resp, q)],
            {resp.id: cf},
            [recent_session],
            [],
        )

        assert result is not None
        assert result.name == "Content"
        assert result.current_score == 82.5
        assert result.target_score == 90

    def test_compute_delivery_dimension(self, feedback_service):
        """Test _compute_delivery_dimension calculation."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        resp, q = self._create_mock_response(recent_session.id, "behavioral")

        af = MagicMock(spec=AudioFeedback)
        af.response_id = resp.id
        af.overall_audio_score = 78.0

        result = feedback_service._compute_delivery_dimension(
            [(resp, q)],
            {resp.id: af},
            [recent_session],
            [],
        )

        assert result is not None
        assert result.name == "Delivery"
        assert result.current_score == 78.0
        assert result.target_score == 85

    def test_compute_behavioral_dimension(self, feedback_service):
        """Test _compute_behavioral_dimension calculation."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        resp, q = self._create_mock_response(recent_session.id, "behavioral")

        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = resp.id
        cf.star_adherence = 80
        cf.answer_structure = 75
        cf.completeness = 70

        result = feedback_service._compute_behavioral_dimension(
            [(resp, q)],
            {resp.id: cf},
            [recent_session],
            [],
        )

        assert result is not None
        assert result.name == "Behavioral"
        # Score = 0.4 * 80 + 0.35 * 75 + 0.25 * 70 = 32 + 26.25 + 17.5 = 75.75
        assert result.current_score == 75.8  # Rounded
        assert result.target_score == 90

    def test_compute_technical_dimension(self, feedback_service):
        """Test _compute_technical_dimension calculation."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        resp, q = self._create_mock_response(recent_session.id, "technical")

        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = resp.id
        cf.technical_accuracy = 85
        cf.completeness = 80
        cf.relevance = 78

        result = feedback_service._compute_technical_dimension(
            [(resp, q)],
            {resp.id: cf},
            [recent_session],
            [],
        )

        assert result is not None
        assert result.name == "Technical"
        assert result.target_score == 85

    def test_compute_system_design_dimension(self, feedback_service):
        """Test _compute_system_design_dimension calculation."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        resp, q = self._create_mock_response(recent_session.id, "system_design")

        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = resp.id
        cf.technical_accuracy = 82
        cf.completeness = 78
        cf.relevance = 85

        result = feedback_service._compute_system_design_dimension(
            [(resp, q)],
            {resp.id: cf},
            [recent_session],
            [],
        )

        assert result is not None
        assert result.name == "System Design"
        assert result.target_score == 80

    def test_compute_communication_dimension(self, feedback_service):
        """Test _compute_communication_dimension calculation."""
        recent_session = MagicMock(spec=InterviewSession)
        recent_session.id = uuid4()

        resp, q = self._create_mock_response(recent_session.id, "behavioral")

        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = resp.id
        cf.relevance = 85
        cf.answer_structure = 80

        result = feedback_service._compute_communication_dimension(
            [(resp, q)],
            {resp.id: cf},
            [recent_session],
            [],
        )

        assert result is not None
        assert result.name == "Communication"
        # Score = 0.5 * 85 + 0.5 * 80 = 42.5 + 40 = 82.5
        assert result.current_score == 82.5
        assert result.target_score == 90

    def test_returns_none_for_empty_recent_scores(self, feedback_service):
        """Test all dimension helpers return None for empty recent scores."""
        previous_session = MagicMock(spec=InterviewSession)
        previous_session.id = uuid4()

        resp, q = self._create_mock_response(previous_session.id, "behavioral")

        cf = MagicMock(spec=ContentFeedback)
        cf.response_id = resp.id
        cf.overall_content_score = 82.5
        cf.relevance = 85
        cf.answer_structure = 80
        cf.star_adherence = 75
        cf.completeness = 70

        # No recent sessions, only previous
        result = feedback_service._compute_content_dimension(
            [(resp, q)],
            {resp.id: cf},
            [],  # No recent sessions
            [previous_session],
        )

        assert result is None


class TestUserImprovementsMocked:
    """Test get_user_improvements with mocked database."""

    @pytest.mark.asyncio
    async def test_returns_not_available_with_less_than_two_sessions(self, feedback_service):
        """Test returns data_available=False with < 2 sessions."""
        mock_session = AsyncMock()

        # Mock exec to return 1 session
        mock_result = MagicMock()
        mock_result.all.return_value = [MagicMock(spec=InterviewSession)]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_user_improvements(mock_session, uuid4())

        assert result["data_available"] is False
        assert result["sessions_analyzed"] == 1

    @pytest.mark.asyncio
    async def test_returns_none_dimensions_with_no_responses(self, feedback_service):
        """Test returns None dimensions when no responses match criteria."""
        mock_session = AsyncMock()
        user_id = uuid4()

        # Create mock sessions
        sessions = []
        for i in range(3):
            s = MagicMock(spec=InterviewSession)
            s.id = uuid4()
            s.created_at = datetime.now(UTC) - timedelta(days=i * 5)
            sessions.append(s)

        # Mock queries: sessions, responses, content feedbacks, audio feedbacks
        mock_results = [
            MagicMock(all=MagicMock(return_value=sessions)),  # Sessions
            MagicMock(all=MagicMock(return_value=[])),  # Responses (empty)
            MagicMock(all=MagicMock(return_value=[])),  # Content feedbacks
            MagicMock(all=MagicMock(return_value=[])),  # Audio feedbacks
        ]

        call_count = 0

        def mock_exec(query):
            nonlocal call_count
            result = mock_results[min(call_count, len(mock_results) - 1)]
            call_count += 1
            return result

        mock_session.exec = AsyncMock(side_effect=mock_exec)

        result = await feedback_service.get_user_improvements(mock_session, user_id)

        assert result["data_available"] is True
        assert result["delivery"] is None
        assert result["behavioral"] is None
        assert result["technical"] is None


class TestSkillsGapMocked:
    """Test get_user_skills_gap with mocked database."""

    @pytest.mark.asyncio
    async def test_returns_empty_with_less_than_two_sessions(self, feedback_service):
        """Test returns empty dimensions with < 2 sessions."""
        mock_session = AsyncMock()

        # Mock exec to return 0 sessions
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await feedback_service.get_user_skills_gap(mock_session, uuid4())

        assert result.data_available is False
        assert result.dimensions == []
        assert result.sessions_analyzed == 0
