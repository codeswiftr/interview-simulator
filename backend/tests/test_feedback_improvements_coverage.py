"""Tests for FeedbackService improvement and skills gap analysis methods.

This module covers the following methods that need additional test coverage:
- get_user_improvements() - aggregate improvement metrics by category
- get_user_skills_gap() - compute skills gap analysis with 6 dimensions
- _aggregate_delivery() - delivery metrics from AudioFeedback
- _aggregate_behavioral() - behavioral metrics (STAR, structure)
- _aggregate_technical() - technical accuracy metrics
- _compute_*_dimension() - skill dimension calculations
- _get_trend() - trend calculation helper
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.feedback import (
    AudioFeedback,
    ContentFeedback,
    SessionFeedback,
    SkillDimension,
)
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.feedback_service import FeedbackService


@pytest.fixture
async def test_user_for_improvements(db_session):
    """Create a test user for improvement tests."""
    user = User(
        email=f"improvements_test_{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password123"),
        experience_level="mid",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def behavioral_question(db_session):
    """Create a behavioral question."""
    question = Question(
        content="Tell me about a time you showed leadership.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def technical_question(db_session):
    """Create a technical question."""
    question = Question(
        content="Explain the differences between REST and GraphQL.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def system_design_question(db_session):
    """Create a system design question."""
    question = Question(
        content="Design a URL shortening service.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        expected_duration_seconds=300,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
def feedback_service():
    """Provide FeedbackService instance."""
    return FeedbackService()


# Test: _get_trend() helper


class TestGetTrend:
    """Tests for the _get_trend helper method."""

    def test_trend_improving_when_current_higher(self, feedback_service):
        """Test trend is 'improving' when current > previous + 2."""
        trend = feedback_service._get_trend(current=85.0, previous=80.0)
        assert trend == "improving"

    def test_trend_declining_when_current_lower(self, feedback_service):
        """Test trend is 'declining' when current < previous - 2."""
        trend = feedback_service._get_trend(current=75.0, previous=80.0)
        assert trend == "declining"

    def test_trend_stable_when_difference_small(self, feedback_service):
        """Test trend is 'stable' when difference <= 2."""
        trend = feedback_service._get_trend(current=81.0, previous=80.0)
        assert trend == "stable"

    def test_trend_stable_at_boundary(self, feedback_service):
        """Test trend is 'stable' at exactly +2 boundary."""
        trend = feedback_service._get_trend(current=82.0, previous=80.0)
        assert trend == "stable"

    def test_trend_improving_just_above_boundary(self, feedback_service):
        """Test trend is 'improving' just above +2 boundary."""
        trend = feedback_service._get_trend(current=82.1, previous=80.0)
        assert trend == "improving"


# Test: get_user_improvements()


class TestGetUserImprovements:
    """Tests for the get_user_improvements method."""

    @pytest.mark.asyncio
    async def test_returns_not_available_with_less_than_two_sessions(
        self, db_session, test_user_for_improvements, feedback_service
    ):
        """Test that improvements return data_available=False with < 2 sessions."""
        # Create only one session
        session = InterviewSession(
            user_id=test_user_for_improvements.id,
            interview_type=InterviewType.BEHAVIORAL,
            status=InterviewStatus.ANALYZED,
        )
        db_session.add(session)
        await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["data_available"] is False
        assert result["sessions_analyzed"] == 1
        assert result["delivery"] is None
        assert result["behavioral"] is None
        assert result["technical"] is None

    @pytest.mark.asyncio
    async def test_returns_delivery_metrics(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that delivery metrics are computed from AudioFeedback."""
        # Create multiple sessions with audio feedback
        sessions = []
        for i in range(6):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=30 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)
            sessions.append(session)

            # Create response
            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Test answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            # Create audio feedback with improving scores over time
            audio_feedback = AudioFeedback(
                response_id=response.id,
                speech_rate_score=70 + i * 3,  # Improving over time
                filler_word_score=75 + i * 2,
                confidence_score=65 + i * 4,
                volume_consistency=80 + i * 2,
                speech_rate_wpm=140,
                filler_words={"um": 2, "uh": 1} if i < 3 else {},
                overall_audio_score=70 + i * 3,
            )
            db_session.add(audio_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["data_available"] is True
        assert result["sessions_analyzed"] >= 2
        assert result["delivery"] is not None
        assert "current_score" in result["delivery"]
        assert "previous_score" in result["delivery"]
        assert "trend" in result["delivery"]
        assert result["delivery"]["trend"] in ["improving", "declining", "stable"]

    @pytest.mark.asyncio
    async def test_returns_behavioral_metrics(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that behavioral metrics are computed for behavioral questions only."""
        # Create sessions with behavioral responses and content feedback
        for i in range(4):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=20 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Behavioral answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            # Content feedback with STAR adherence
            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=0,  # Not relevant for behavioral
                star_adherence=70 + i * 5,
                answer_structure=75 + i * 4,
                completeness=65 + i * 6,
                relevance=80,
                overall_content_score=72 + i * 5,
                strengths=["Good STAR method"] if i > 1 else [],
                improvements=["Improve STAR method"] if i < 2 else [],
                detailed_feedback="Test feedback",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["data_available"] is True
        assert result["behavioral"] is not None
        assert "current_score" in result["behavioral"]
        assert "trend" in result["behavioral"]
        assert "improvements" in result["behavioral"]
        assert "areas_to_work_on" in result["behavioral"]

    @pytest.mark.asyncio
    async def test_returns_technical_metrics(
        self,
        db_session,
        test_user_for_improvements,
        technical_question,
        system_design_question,
        feedback_service,
    ):
        """Test that technical metrics are computed for technical/system_design questions."""
        questions = [technical_question, system_design_question]

        for i in range(4):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.TECHNICAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=20 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=questions[i % 2].id,
                transcript=f"Technical answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=75 + i * 4,
                star_adherence=0,
                answer_structure=70 + i * 3,
                completeness=72 + i * 5,
                relevance=78 + i * 3,
                overall_content_score=74 + i * 4,
                strengths=["Good technical depth"] if i > 1 else [],
                improvements=["Add trade-off analysis"] if i < 2 else [],
                detailed_feedback="Test feedback",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["data_available"] is True
        assert result["technical"] is not None
        assert "current_score" in result["technical"]
        assert "trend" in result["technical"]


# Test: get_user_skills_gap()


class TestGetUserSkillsGap:
    """Tests for the get_user_skills_gap method."""

    @pytest.mark.asyncio
    async def test_returns_empty_with_less_than_two_sessions(
        self, db_session, test_user_for_improvements, feedback_service
    ):
        """Test that skills gap returns empty dimensions with < 2 sessions."""
        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        assert result.data_available is False
        assert result.dimensions == []
        assert result.sessions_analyzed == 0

    @pytest.mark.asyncio
    async def test_computes_content_dimension(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that Content dimension is computed from overall_content_score."""
        # Create sessions with content feedback
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=70,
                star_adherence=75,
                answer_structure=80,
                completeness=72,
                relevance=85,
                overall_content_score=76 + i * 3,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        assert result.data_available is True
        assert len(result.dimensions) > 0

        content_dim = next(
            (d for d in result.dimensions if d.name == "Content"), None
        )
        assert content_dim is not None
        assert content_dim.target_score == 90
        assert content_dim.trend in ["improving", "declining", "stable"]

    @pytest.mark.asyncio
    async def test_computes_delivery_dimension(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that Delivery dimension is computed from audio feedback."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            audio_feedback = AudioFeedback(
                response_id=response.id,
                speech_rate_score=75,
                filler_word_score=80,
                confidence_score=70,
                volume_consistency=78,
                overall_audio_score=76 + i * 2,
            )
            db_session.add(audio_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        delivery_dim = next(
            (d for d in result.dimensions if d.name == "Delivery"), None
        )
        assert delivery_dim is not None
        assert delivery_dim.target_score == 85

    @pytest.mark.asyncio
    async def test_computes_behavioral_dimension(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that Behavioral dimension is computed for behavioral questions."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Behavioral answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=0,
                star_adherence=80 + i * 3,  # Key metric for behavioral
                answer_structure=75 + i * 2,
                completeness=70 + i * 4,
                relevance=85,
                overall_content_score=78,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        behavioral_dim = next(
            (d for d in result.dimensions if d.name == "Behavioral"), None
        )
        assert behavioral_dim is not None
        assert behavioral_dim.target_score == 90

    @pytest.mark.asyncio
    async def test_computes_technical_dimension(
        self,
        db_session,
        test_user_for_improvements,
        technical_question,
        feedback_service,
    ):
        """Test that Technical dimension is computed for technical questions."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.TECHNICAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=technical_question.id,
                transcript=f"Technical answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=75 + i * 4,  # Key metric for technical
                star_adherence=0,
                answer_structure=70,
                completeness=72 + i * 3,
                relevance=80 + i * 2,
                overall_content_score=74 + i * 3,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        technical_dim = next(
            (d for d in result.dimensions if d.name == "Technical"), None
        )
        assert technical_dim is not None
        assert technical_dim.target_score == 85

    @pytest.mark.asyncio
    async def test_computes_system_design_dimension(
        self,
        db_session,
        test_user_for_improvements,
        system_design_question,
        feedback_service,
    ):
        """Test that System Design dimension is computed for system_design questions."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.SYSTEM_DESIGN,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=system_design_question.id,
                transcript=f"System design answer {i}",
                duration_seconds=300,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=78 + i * 3,
                star_adherence=0,
                answer_structure=75,
                completeness=70 + i * 4,
                relevance=82 + i * 2,
                overall_content_score=76 + i * 3,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        system_design_dim = next(
            (d for d in result.dimensions if d.name == "System Design"), None
        )
        assert system_design_dim is not None
        assert system_design_dim.target_score == 80

    @pytest.mark.asyncio
    async def test_computes_communication_dimension(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that Communication dimension is computed from relevance + structure."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=70,
                star_adherence=75,
                answer_structure=80 + i * 2,  # Part of communication
                completeness=72,
                relevance=85 + i * 2,  # Part of communication
                overall_content_score=78,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        communication_dim = next(
            (d for d in result.dimensions if d.name == "Communication"), None
        )
        assert communication_dim is not None
        assert communication_dim.target_score == 90

    @pytest.mark.asyncio
    async def test_returns_last_updated_timestamp(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that last_updated is returned with timezone."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=70,
                star_adherence=75,
                answer_structure=80,
                completeness=72,
                relevance=85,
                overall_content_score=78,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_skills_gap(
            db_session, test_user_for_improvements.id
        )

        assert result.last_updated is not None
        # Check timezone awareness
        assert result.last_updated.tzinfo is not None or result.last_updated.tzinfo == UTC


# Test: Edge cases for aggregate methods


class TestAggregateMethodsEdgeCases:
    """Test edge cases in the aggregate helper methods."""

    @pytest.mark.asyncio
    async def test_delivery_insights_for_low_scores(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that delivery insights capture low score areas."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            # Low scores to trigger improvement suggestions
            audio_feedback = AudioFeedback(
                response_id=response.id,
                speech_rate_score=50,  # Low - should suggest pacing
                filler_word_score=45,  # Low - should suggest reducing fillers
                confidence_score=55,  # Low - should suggest confidence
                volume_consistency=48,  # Low - should suggest volume
                speech_rate_wpm=180,  # Too fast
                filler_words={"um": 10, "uh": 8},  # High filler count
                overall_audio_score=50,
            )
            db_session.add(audio_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["delivery"] is not None
        assert len(result["delivery"]["areas_to_work_on"]) > 0

    @pytest.mark.asyncio
    async def test_delivery_insights_for_high_scores(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that delivery insights capture high score achievements."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            # High scores to trigger improvement recognition
            audio_feedback = AudioFeedback(
                response_id=response.id,
                speech_rate_score=85,
                filler_word_score=90,
                confidence_score=88,
                volume_consistency=85,
                speech_rate_wpm=135,  # Optimal
                filler_words={},  # No fillers
                overall_audio_score=87,
            )
            db_session.add(audio_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["delivery"] is not None
        assert len(result["delivery"]["improvements"]) > 0

    @pytest.mark.asyncio
    async def test_behavioral_insights_from_feedback_strengths(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that behavioral insights extract from strengths/improvements lists."""
        for i in range(3):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=15 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Behavioral answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=0,
                star_adherence=85,
                answer_structure=80,
                completeness=75,
                relevance=85,
                overall_content_score=81,
                strengths=["Great STAR method usage", "Good structure"],
                improvements=["Improve structure clarity"],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["behavioral"] is not None


# Test: Session filtering and ordering


class TestSessionFilteringAndOrdering:
    """Test that sessions are properly filtered and ordered."""

    @pytest.mark.asyncio
    async def test_only_completed_and_analyzed_sessions_included(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that only COMPLETED and ANALYZED sessions are included."""
        # Create sessions with different statuses
        for status in [
            InterviewStatus.SCHEDULED,
            InterviewStatus.IN_PROGRESS,
            InterviewStatus.COMPLETED,
            InterviewStatus.ANALYZED,
            InterviewStatus.CANCELLED,
        ]:
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=status,
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            if status in [InterviewStatus.COMPLETED, InterviewStatus.ANALYZED]:
                response = InterviewResponse(
                    session_id=session.id,
                    question_id=behavioral_question.id,
                    transcript="Test answer",
                    duration_seconds=120,
                )
                db_session.add(response)
                await db_session.commit()
                await db_session.refresh(response)

                content_feedback = ContentFeedback(
                    response_id=response.id,
                    technical_accuracy=70,
                    star_adherence=75,
                    answer_structure=80,
                    completeness=72,
                    relevance=85,
                    overall_content_score=76,
                    strengths=[],
                    improvements=[],
                    detailed_feedback="Test",
                )
                db_session.add(content_feedback)
                await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        # Should have exactly 2 sessions (COMPLETED and ANALYZED)
        assert result["sessions_analyzed"] == 2

    @pytest.mark.asyncio
    async def test_sessions_ordered_by_created_at_descending(
        self,
        db_session,
        test_user_for_improvements,
        behavioral_question,
        feedback_service,
    ):
        """Test that recent sessions are used for 'current' and older for 'previous'."""
        # Create sessions with explicit ordering
        for i in range(10):
            session = InterviewSession(
                user_id=test_user_for_improvements.id,
                interview_type=InterviewType.BEHAVIORAL,
                status=InterviewStatus.ANALYZED,
                created_at=datetime.now(UTC) - timedelta(days=50 - i * 5),
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            response = InterviewResponse(
                session_id=session.id,
                question_id=behavioral_question.id,
                transcript=f"Answer {i}",
                duration_seconds=120,
            )
            db_session.add(response)
            await db_session.commit()
            await db_session.refresh(response)

            # Improve scores over time to verify trend calculation
            content_feedback = ContentFeedback(
                response_id=response.id,
                technical_accuracy=70,
                star_adherence=60 + i * 3,  # Improves with newer sessions
                answer_structure=65 + i * 2,
                completeness=70 + i * 2,
                relevance=85,
                overall_content_score=70 + i * 2,
                strengths=[],
                improvements=[],
                detailed_feedback="Test",
            )
            db_session.add(content_feedback)
            await db_session.commit()

        result = await feedback_service.get_user_improvements(
            db_session, test_user_for_improvements.id
        )

        assert result["sessions_analyzed"] == 10
        # Recent sessions should show higher scores (improving trend)
        if result["behavioral"]:
            assert result["behavioral"]["current_score"] >= result["behavioral"]["previous_score"]
