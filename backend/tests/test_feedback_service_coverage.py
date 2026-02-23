"""Comprehensive service-level tests for feedback_service.py to improve coverage.

This test module specifically targets coverage gaps in FeedbackService:
- generate_feedback() response validation and error handling
- generate_video_feedback() path validation
- get_response_feedback() / get_video_feedback() / get_session_feedback() retrieval
- get_processing_summary() status tracking
- get_user_progress() aggregation
"""

from uuid import uuid4

import pytest

from app.models.feedback import ContentFeedback, SessionFeedback, VideoFeedback
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
    ProcessingStatus,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.feedback_service import FeedbackService

# Use shared fixtures from conftest.py (db_session, clean_database, etc.)


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email="feedbacktest@example.com",
        hashed_password=hash_password("password123"),
        experience_level="mid",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_question(db_session):
    """Create a test question."""
    question = Question(
        content="Tell me about a challenging project.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def test_interview(db_session, test_user):
    """Create a test interview session."""
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
        question_count=1,
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    return interview


@pytest.fixture
async def test_response(db_session, test_interview, test_question):
    """Create a test interview response."""
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="This is my test response about a challenging project.",
        duration_seconds=120,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)
    return response


@pytest.fixture
def feedback_service():
    """Provide an instance of FeedbackService."""
    return FeedbackService()


# Test: FeedbackService initialization


@pytest.mark.asyncio
async def test_feedback_service_initializes_dependencies(feedback_service):
    """Test that FeedbackService initializes with required analyzers."""
    from app.ai.content_analyzer import ContentAnalyzer
    from app.services.video_service import VideoService

    assert hasattr(feedback_service, "content_analyzer")
    assert isinstance(feedback_service.content_analyzer, ContentAnalyzer)
    assert hasattr(feedback_service, "video_service")
    assert isinstance(feedback_service.video_service, VideoService)


# Test: generate_feedback() error handling


@pytest.mark.asyncio
async def test_generate_feedback_raises_error_when_response_not_found(db_session, feedback_service):
    """Test that generate_feedback raises ValueError for non-existent response."""
    fake_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_feedback(db_session, fake_id)

    assert "not found" in str(exc_info.value)
    assert str(fake_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_feedback_raises_error_when_feedback_already_exists(
    db_session, test_response, feedback_service
):
    """Test that generate_feedback raises ValueError when feedback exists."""
    # Create existing feedback
    existing_feedback = ContentFeedback(
        response_id=test_response.id,
        technical_accuracy=80,
        star_adherence=75,
        answer_structure=85,
        completeness=70,
        relevance=90,
        overall_content_score=80,
        strengths=["Good structure"],
        improvements=["Add more details"],
        detailed_feedback="Good answer overall.",
    )
    db_session.add(existing_feedback)
    await db_session.commit()

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_feedback(db_session, test_response.id)

    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_feedback_raises_error_when_no_transcript(
    db_session, test_interview, test_question, feedback_service
):
    """Test that generate_feedback raises ValueError when response has no transcript."""
    # Create response without transcript
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript=None,  # No transcript
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_feedback(db_session, response.id)

    assert "no transcript" in str(exc_info.value)


# Test: get_response_feedback()


@pytest.mark.asyncio
async def test_get_response_feedback_returns_feedback_when_exists(
    db_session, test_response, feedback_service
):
    """Test that get_response_feedback returns feedback when it exists."""
    # Create feedback
    feedback = ContentFeedback(
        response_id=test_response.id,
        technical_accuracy=85,
        star_adherence=80,
        answer_structure=75,
        completeness=70,
        relevance=85,
        overall_content_score=79,
        strengths=["Clear examples"],
        improvements=["More concise"],
        detailed_feedback="Well structured.",
    )
    db_session.add(feedback)
    await db_session.commit()

    result = await feedback_service.get_response_feedback(db_session, test_response.id)

    assert result is not None
    assert result.response_id == test_response.id
    assert result.overall_content_score == 79


@pytest.mark.asyncio
async def test_get_response_feedback_returns_none_when_not_exists(
    db_session, test_response, feedback_service
):
    """Test that get_response_feedback returns None when no feedback exists."""
    result = await feedback_service.get_response_feedback(db_session, test_response.id)

    assert result is None


@pytest.mark.asyncio
async def test_get_response_feedback_for_nonexistent_response(db_session, feedback_service):
    """Test get_response_feedback with non-existent response ID."""
    fake_id = uuid4()
    result = await feedback_service.get_response_feedback(db_session, fake_id)

    assert result is None


# Test: get_video_feedback()


@pytest.mark.asyncio
async def test_get_video_feedback_returns_feedback_when_exists(
    db_session, test_response, feedback_service
):
    """Test that get_video_feedback returns feedback when it exists."""
    # Create video feedback
    video_feedback = VideoFeedback(
        response_id=test_response.id,
        confidence_score=0.85,
        nervousness_score=0.15,
        engagement_score=0.80,
        eye_contact_percentage=0.75,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )
    db_session.add(video_feedback)
    await db_session.commit()

    result = await feedback_service.get_video_feedback(db_session, test_response.id)

    assert result is not None
    assert result.response_id == test_response.id
    assert result.confidence_score == 0.85


@pytest.mark.asyncio
async def test_get_video_feedback_returns_none_when_not_exists(
    db_session, test_response, feedback_service
):
    """Test that get_video_feedback returns None when no feedback exists."""
    result = await feedback_service.get_video_feedback(db_session, test_response.id)

    assert result is None


# Test: generate_video_feedback()


@pytest.mark.asyncio
async def test_generate_video_feedback_raises_error_when_response_not_found(
    db_session, feedback_service
):
    """Test generate_video_feedback raises ValueError for non-existent response."""
    fake_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_video_feedback(db_session, fake_id)

    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_video_feedback_raises_error_when_no_video(
    db_session, test_response, feedback_service
):
    """Test generate_video_feedback raises ValueError when no video attached."""
    # test_response has no video_url
    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_video_feedback(db_session, test_response.id)

    assert "no video attached" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_video_feedback_raises_error_when_feedback_exists(
    db_session, test_interview, test_question, feedback_service
):
    """Test generate_video_feedback raises ValueError when feedback already exists."""
    # Create response with video
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Test transcript",
        video_url="/uploads/video/test.webm",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    # Create existing video feedback
    video_feedback = VideoFeedback(
        response_id=response.id,
        confidence_score=0.80,
        nervousness_score=0.20,
        engagement_score=0.75,
        eye_contact_percentage=0.70,
        looking_away_count=5,
        fidget_count=3,
        hand_gesture_frequency=0.3,
        processing_duration_ms=2000,
        frame_count=40,
    )
    db_session.add(video_feedback)
    await db_session.commit()

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_video_feedback(db_session, response.id)

    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_video_feedback_raises_error_when_video_file_not_found(
    db_session, test_interview, test_question, feedback_service
):
    """Test generate_video_feedback raises ValueError when video file doesn't exist."""
    # Create response with non-existent video path
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Test transcript",
        video_url="/uploads/video/nonexistent_video_12345.webm",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_video_feedback(db_session, response.id)

    assert "not found" in str(exc_info.value)


# Test: get_session_feedback()


@pytest.mark.asyncio
async def test_get_session_feedback_returns_feedback_when_exists(
    db_session, test_interview, feedback_service
):
    """Test that get_session_feedback returns feedback when it exists."""
    # Create session feedback
    session_feedback = SessionFeedback(
        session_id=test_interview.id,
        overall_score=82.5,
        audio_score=75.0,
        content_score=85.0,
        top_strengths=["Clear communication", "Good examples"],
        top_improvements=["More concise", "Better structure"],
        recommended_practice_areas=["Technical accuracy"],
        next_question_ids=[],
    )
    db_session.add(session_feedback)
    await db_session.commit()

    result = await feedback_service.get_session_feedback(db_session, test_interview.id)

    assert result is not None
    assert result.session_id == test_interview.id
    assert result.overall_score == 82.5


@pytest.mark.asyncio
async def test_get_session_feedback_returns_none_when_not_exists(
    db_session, test_interview, feedback_service
):
    """Test that get_session_feedback returns None when no feedback exists."""
    result = await feedback_service.get_session_feedback(db_session, test_interview.id)

    assert result is None


# Test: get_all_session_feedbacks()


@pytest.mark.asyncio
async def test_get_all_session_feedbacks_returns_ordered_list(
    db_session, test_interview, test_question, feedback_service
):
    """Test that get_all_session_feedbacks returns all feedbacks ordered by created_at."""
    # Create multiple responses
    response1 = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="First response",
        duration_seconds=60,
    )
    response2 = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Second response",
        duration_seconds=90,
    )
    db_session.add_all([response1, response2])
    await db_session.commit()
    await db_session.refresh(response1)
    await db_session.refresh(response2)

    # Create feedbacks
    feedback1 = ContentFeedback(
        response_id=response1.id,
        technical_accuracy=70,
        star_adherence=65,
        answer_structure=75,
        completeness=60,
        relevance=80,
        overall_content_score=70,
        strengths=["Quick thinking"],
        improvements=["More detail"],
        detailed_feedback="Good start.",
    )
    feedback2 = ContentFeedback(
        response_id=response2.id,
        technical_accuracy=85,
        star_adherence=80,
        answer_structure=85,
        completeness=75,
        relevance=90,
        overall_content_score=83,
        strengths=["Thorough"],
        improvements=["Pace"],
        detailed_feedback="Excellent.",
    )
    db_session.add_all([feedback1, feedback2])
    await db_session.commit()

    result = await feedback_service.get_all_session_feedbacks(db_session, test_interview.id)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_all_session_feedbacks_returns_empty_list_when_none(
    db_session, test_interview, feedback_service
):
    """Test that get_all_session_feedbacks returns empty list when no feedbacks."""
    result = await feedback_service.get_all_session_feedbacks(db_session, test_interview.id)

    assert result == []


# Test: get_processing_summary()


@pytest.mark.asyncio
async def test_get_processing_summary_returns_correct_counts(
    db_session, test_interview, test_question, feedback_service
):
    """Test that get_processing_summary returns correct status counts."""
    # Create responses with different statuses
    response1 = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Completed",
        duration_seconds=60,
        processing_status=ProcessingStatus.COMPLETED,
    )
    response2 = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Transcribing",
        duration_seconds=60,
        processing_status=ProcessingStatus.TRANSCRIBING,
    )
    response3 = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        duration_seconds=60,
        processing_status=ProcessingStatus.PENDING,
    )
    db_session.add_all([response1, response2, response3])
    await db_session.commit()

    result = await feedback_service.get_processing_summary(db_session, test_interview.id)

    assert result["total_responses"] == 3
    assert result["status_counts"]["completed"] == 1
    assert result["status_counts"]["transcribing"] == 1
    assert result["status_counts"]["pending"] == 1
    assert result["has_session_feedback"] is False
    assert result["all_processed"] is False
    assert result["current_step"] == "transcribing"


@pytest.mark.asyncio
async def test_get_processing_summary_shows_complete_when_all_done(
    db_session, test_interview, test_question, feedback_service
):
    """Test that get_processing_summary shows complete when all responses processed."""
    # Create completed responses
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Done",
        duration_seconds=60,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db_session.add(response)
    await db_session.commit()

    # Create session feedback
    session_feedback = SessionFeedback(
        session_id=test_interview.id,
        overall_score=85,
        audio_score=80,
        content_score=85,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=[],
        next_question_ids=[],
    )
    db_session.add(session_feedback)
    await db_session.commit()

    result = await feedback_service.get_processing_summary(db_session, test_interview.id)

    assert result["has_session_feedback"] is True
    assert result["all_processed"] is True
    assert result["current_step"] == "complete"


@pytest.mark.asyncio
async def test_get_processing_summary_shows_analyzing_state(
    db_session, test_interview, test_question, feedback_service
):
    """Test that get_processing_summary shows analyzing when response is being analyzed."""
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Being analyzed",
        duration_seconds=60,
        processing_status=ProcessingStatus.ANALYZING,
    )
    db_session.add(response)
    await db_session.commit()

    result = await feedback_service.get_processing_summary(db_session, test_interview.id)

    assert result["current_step"] == "analyzing"


@pytest.mark.asyncio
async def test_get_processing_summary_shows_generating_feedback_state(
    db_session, test_interview, test_question, feedback_service
):
    """Test get_processing_summary shows generating_feedback when responses done but no session feedback."""
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        transcript="Done",
        duration_seconds=60,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db_session.add(response)
    await db_session.commit()

    result = await feedback_service.get_processing_summary(db_session, test_interview.id)

    assert result["current_step"] == "generating_feedback"


@pytest.mark.asyncio
async def test_get_processing_summary_shows_failed_state(
    db_session, test_interview, test_question, feedback_service
):
    """Test get_processing_summary shows failed when all responses failed."""
    response = InterviewResponse(
        session_id=test_interview.id,
        question_id=test_question.id,
        duration_seconds=60,
        processing_status=ProcessingStatus.FAILED,
    )
    db_session.add(response)
    await db_session.commit()

    result = await feedback_service.get_processing_summary(db_session, test_interview.id)

    assert result["current_step"] == "failed"
    assert result["status_counts"]["failed"] == 1


@pytest.mark.asyncio
async def test_get_processing_summary_empty_session(db_session, test_interview, feedback_service):
    """Test get_processing_summary with no responses."""
    result = await feedback_service.get_processing_summary(db_session, test_interview.id)

    assert result["total_responses"] == 0
    assert result["all_processed"] is False
    assert result["current_step"] == "idle"


# Test: get_user_progress()


@pytest.mark.asyncio
async def test_get_user_progress_returns_empty_for_new_user(
    db_session, test_user, feedback_service
):
    """Test that get_user_progress returns empty metrics for user with no sessions."""
    result = await feedback_service.get_user_progress(db_session, test_user.id)

    assert result["recommended_practice_areas"] == []
    assert result["average_audio_score"] is None
    assert result["average_content_score"] is None


@pytest.mark.asyncio
async def test_get_user_progress_calculates_averages(db_session, test_user, feedback_service):
    """Test that get_user_progress calculates correct averages."""
    # Create completed sessions
    session1 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.ANALYZED,
        question_count=1,
    )
    session2 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.COMPLETED,
        question_count=1,
    )
    db_session.add_all([session1, session2])
    await db_session.commit()
    await db_session.refresh(session1)
    await db_session.refresh(session2)

    # Create session feedbacks
    feedback1 = SessionFeedback(
        session_id=session1.id,
        overall_score=80,
        audio_score=75,
        content_score=85,
        top_strengths=["Clear"],
        top_improvements=["Pace"],
        recommended_practice_areas=["Technical accuracy"],
        next_question_ids=[],
    )
    feedback2 = SessionFeedback(
        session_id=session2.id,
        overall_score=90,
        audio_score=85,
        content_score=95,
        top_strengths=["Thorough"],
        top_improvements=["Concise"],
        recommended_practice_areas=["Technical accuracy", "STAR method"],
        next_question_ids=[],
    )
    db_session.add_all([feedback1, feedback2])
    await db_session.commit()

    result = await feedback_service.get_user_progress(db_session, test_user.id)

    # Average audio: (75 + 85) / 2 = 80
    assert result["average_audio_score"] == 80.0
    # Average content: (85 + 95) / 2 = 90
    assert result["average_content_score"] == 90.0
    # Most common practice area
    assert "Technical accuracy" in result["recommended_practice_areas"]


@pytest.mark.asyncio
async def test_get_user_progress_returns_empty_for_sessions_without_feedback(
    db_session, test_user, feedback_service
):
    """Test get_user_progress returns empty when sessions have no feedback."""
    # Create completed session without feedback
    session = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.COMPLETED,
        question_count=1,
    )
    db_session.add(session)
    await db_session.commit()

    result = await feedback_service.get_user_progress(db_session, test_user.id)

    assert result["recommended_practice_areas"] == []
    assert result["average_audio_score"] is None
    assert result["average_content_score"] is None


@pytest.mark.asyncio
async def test_get_user_progress_with_mixed_audio_scores(db_session, test_user, feedback_service):
    """Test get_user_progress calculates averages with real audio scores."""
    session1 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.ANALYZED,
        question_count=1,
    )
    session2 = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.ANALYZED,
        question_count=1,
    )
    db_session.add_all([session1, session2])
    await db_session.commit()
    await db_session.refresh(session1)
    await db_session.refresh(session2)

    # One session with audio, one without (using 0.0)
    feedback1 = SessionFeedback(
        session_id=session1.id,
        overall_score=80,
        audio_score=70.0,
        content_score=85,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=["Technical accuracy"],
        next_question_ids=[],
    )
    feedback2 = SessionFeedback(
        session_id=session2.id,
        overall_score=85,
        audio_score=80.0,
        content_score=90,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=["STAR method"],
        next_question_ids=[],
    )
    db_session.add_all([feedback1, feedback2])
    await db_session.commit()

    result = await feedback_service.get_user_progress(db_session, test_user.id)

    # Average audio: (70 + 80) / 2 = 75
    assert result["average_audio_score"] == 75.0
    # Average content: (85 + 90) / 2 = 87.5
    assert result["average_content_score"] == 87.5
    # Practice areas from both sessions
    assert len(result["recommended_practice_areas"]) >= 1


# Test: generate_session_feedback() error handling


@pytest.mark.asyncio
async def test_generate_session_feedback_raises_error_when_session_not_found(
    db_session, feedback_service
):
    """Test generate_session_feedback raises ValueError for non-existent session."""
    fake_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_session_feedback(db_session, fake_id)

    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_session_feedback_raises_error_when_feedback_exists(
    db_session, test_interview, feedback_service
):
    """Test generate_session_feedback raises ValueError when feedback already exists."""
    # Create existing session feedback
    existing = SessionFeedback(
        session_id=test_interview.id,
        overall_score=85,
        audio_score=80,
        content_score=90,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=[],
        next_question_ids=[],
    )
    db_session.add(existing)
    await db_session.commit()

    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_session_feedback(db_session, test_interview.id)

    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_session_feedback_raises_error_when_no_responses(
    db_session, test_interview, feedback_service
):
    """Test generate_session_feedback raises ValueError when session has no responses."""
    with pytest.raises(ValueError) as exc_info:
        await feedback_service.generate_session_feedback(db_session, test_interview.id)

    assert "No responses found" in str(exc_info.value)
