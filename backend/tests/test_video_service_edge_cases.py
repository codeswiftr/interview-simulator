"""Additional edge case tests for video_service.py to improve coverage.

Focuses on edge cases, error paths, and metric variations not covered
by existing tests.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.ai.video_analyzer import VideoMetrics
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
from app.services.video_service import VideoService


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email=f"videoedge_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_response(db_session, test_user):
    """Create a test interview response."""
    question = Question(
        content="Test question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Test transcript",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)
    return response


@pytest.fixture
def video_service():
    """Provide VideoService instance."""
    return VideoService()


@pytest.fixture
def extreme_metrics():
    """Provide extreme edge case metrics."""
    return VideoMetrics(
        confidence_score=0.0,  # Minimum
        nervousness_score=1.0,  # Maximum
        engagement_score=0.0,
        eye_contact_percentage=0.0,
        looking_away_count=0,
        fidget_count=0,
        hand_gesture_frequency=0.0,
        processing_duration_ms=0,
        frame_count=1,  # Minimal frames
    )


# Test: Zero-value metrics
@pytest.mark.asyncio
async def test_save_video_feedback_with_zero_values(
    db_session, test_response, video_service, extreme_metrics
):
    """Test saving feedback with zero/extreme values."""
    feedback = await video_service.save_video_feedback(
        db_session, test_response.id, extreme_metrics
    )

    assert feedback.confidence_score == 0.0
    assert feedback.nervousness_score == 1.0
    assert feedback.engagement_score == 0.0
    assert feedback.eye_contact_percentage == 0.0
    assert feedback.looking_away_count == 0
    assert feedback.fidget_count == 0
    assert feedback.hand_gesture_frequency == 0.0
    assert feedback.processing_duration_ms == 0
    assert feedback.frame_count == 1


# Test: Maximum value metrics
@pytest.mark.asyncio
async def test_save_video_feedback_with_maximum_values(db_session, test_response, video_service):
    """Test saving feedback with maximum values."""
    max_metrics = VideoMetrics(
        confidence_score=1.0,
        nervousness_score=0.0,
        engagement_score=1.0,
        eye_contact_percentage=1.0,
        looking_away_count=999,
        fidget_count=999,
        hand_gesture_frequency=10.0,
        processing_duration_ms=999999,
        frame_count=99999,
    )

    feedback = await video_service.save_video_feedback(db_session, test_response.id, max_metrics)

    assert feedback.confidence_score == 1.0
    assert feedback.looking_away_count == 999
    assert feedback.frame_count == 99999


# Test: analyze_video with different file extensions
@pytest.mark.asyncio
async def test_analyze_video_with_webm_file(db_session, test_response, video_service, tmp_path):
    """Test analyze_video works with .webm files."""
    video_file = tmp_path / "test.webm"
    video_file.write_bytes(b"webm content")

    sample_metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )

    with patch.object(
        video_service.analyzer, "analyze", new=AsyncMock(return_value=sample_metrics)
    ):
        result = await video_service.analyze_video(db_session, test_response.id, str(video_file))

    assert result == sample_metrics


# Test: analyze_video with different file extensions
@pytest.mark.asyncio
async def test_analyze_video_with_mp4_file(db_session, test_response, video_service, tmp_path):
    """Test analyze_video works with .mp4 files."""
    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"mp4 content")

    sample_metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )

    with patch.object(
        video_service.analyzer, "analyze", new=AsyncMock(return_value=sample_metrics)
    ):
        result = await video_service.analyze_video(db_session, test_response.id, str(video_file))

    assert result == sample_metrics


# Test: Video file path with spaces
@pytest.mark.asyncio
async def test_analyze_video_with_path_containing_spaces(
    db_session, test_response, video_service, tmp_path
):
    """Test analyze_video handles paths with spaces."""
    video_dir = tmp_path / "video files"
    video_dir.mkdir()
    video_file = video_dir / "my video.mp4"
    video_file.write_bytes(b"content")

    sample_metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )

    with patch.object(
        video_service.analyzer, "analyze", new=AsyncMock(return_value=sample_metrics)
    ):
        result = await video_service.analyze_video(db_session, test_response.id, str(video_file))

    assert result == sample_metrics


# Test: process_response_video with minimal video
@pytest.mark.asyncio
async def test_process_response_video_with_minimal_metrics(
    db_session, test_response, video_service, extreme_metrics, tmp_path
):
    """Test process_response_video with minimal/extreme metrics."""
    video_file = tmp_path / "minimal.mp4"
    video_file.write_bytes(b"min")

    with patch.object(
        video_service.analyzer, "analyze", new=AsyncMock(return_value=extreme_metrics)
    ):
        feedback = await video_service.process_response_video(
            db_session, test_response.id, str(video_file)
        )

    assert feedback.confidence_score == 0.0
    assert feedback.frame_count == 1


# Test: Multiple responses for same session
@pytest.mark.asyncio
async def test_save_video_feedback_for_multiple_responses_same_session(
    db_session, test_user, video_service
):
    """Test saving video feedback for multiple responses in same session."""
    question = Question(
        content="Question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    # Create two responses for same session
    response1 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer 1",
        duration_seconds=100,
    )
    response2 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer 2",
        duration_seconds=120,
    )
    db_session.add_all([response1, response2])
    await db_session.commit()
    await db_session.refresh(response1)
    await db_session.refresh(response2)

    metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )

    # Save feedback for both
    feedback1 = await video_service.save_video_feedback(db_session, response1.id, metrics)
    feedback2 = await video_service.save_video_feedback(db_session, response2.id, metrics)

    assert feedback1.response_id == response1.id
    assert feedback2.response_id == response2.id
    assert feedback1.id != feedback2.id


# Test: Response with different processing statuses
@pytest.mark.asyncio
async def test_get_response_with_pending_status(db_session, test_user, video_service):
    """Test _get_response works with PENDING processing status."""
    question = Question(
        content="Question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer",
        duration_seconds=100,
        processing_status=ProcessingStatus.PENDING,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    result = await video_service._get_response(db_session, response.id)

    assert result.processing_status == ProcessingStatus.PENDING


# Test: Response with FAILED status
@pytest.mark.asyncio
async def test_get_response_with_failed_status(db_session, test_user, video_service):
    """Test _get_response works with FAILED processing status."""
    question = Question(
        content="Question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer",
        duration_seconds=100,
        processing_status=ProcessingStatus.FAILED,
        processing_error="Test error",
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    result = await video_service._get_response(db_session, response.id)

    assert result.processing_status == ProcessingStatus.FAILED
    assert result.processing_error == "Test error"


# Test: Feedback precision
@pytest.mark.asyncio
async def test_save_video_feedback_preserves_decimal_precision(
    db_session, test_response, video_service
):
    """Test that decimal values are preserved accurately."""
    precise_metrics = VideoMetrics(
        confidence_score=0.847392,
        nervousness_score=0.152608,
        engagement_score=0.912345,
        eye_contact_percentage=0.678901,
        looking_away_count=7,
        fidget_count=4,
        hand_gesture_frequency=0.543210,
        processing_duration_ms=1234,
        frame_count=456,
    )

    feedback = await video_service.save_video_feedback(
        db_session, test_response.id, precise_metrics
    )

    # Check precision is preserved
    assert abs(feedback.confidence_score - 0.847392) < 0.000001
    assert abs(feedback.nervousness_score - 0.152608) < 0.000001
    assert abs(feedback.engagement_score - 0.912345) < 0.000001
    assert abs(feedback.eye_contact_percentage - 0.678901) < 0.000001
    assert abs(feedback.hand_gesture_frequency - 0.543210) < 0.000001


# Test: Empty video file
@pytest.mark.asyncio
async def test_analyze_video_with_empty_file(db_session, test_response, video_service, tmp_path):
    """Test analyze_video with empty file (exists but has no content)."""
    video_file = tmp_path / "empty.mp4"
    video_file.touch()  # Create empty file

    sample_metrics = VideoMetrics(
        confidence_score=0.0,
        nervousness_score=0.0,
        engagement_score=0.0,
        eye_contact_percentage=0.0,
        looking_away_count=0,
        fidget_count=0,
        hand_gesture_frequency=0.0,
        processing_duration_ms=0,
        frame_count=0,
    )

    with patch.object(
        video_service.analyzer, "analyze", new=AsyncMock(return_value=sample_metrics)
    ):
        result = await video_service.analyze_video(db_session, test_response.id, str(video_file))

    assert result == sample_metrics


# Test: File path edge cases
@pytest.mark.asyncio
async def test_analyze_video_with_relative_path_nonexistent(
    db_session, test_response, video_service
):
    """Test analyze_video with relative path that doesn't exist."""
    with pytest.raises(ValueError) as exc_info:
        await video_service.analyze_video(db_session, test_response.id, "./nonexistent/video.mp4")

    assert "Video file not found" in str(exc_info.value)


# Test: Response without video_url
@pytest.mark.asyncio
async def test_get_response_without_video_url(db_session, test_user, video_service):
    """Test _get_response works for response without video URL."""
    question = Question(
        content="Question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    response = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer",
        duration_seconds=100,
        video_url=None,  # No video URL
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    result = await video_service._get_response(db_session, response.id)

    assert result.video_url is None


# Test: Large frame count
@pytest.mark.asyncio
async def test_save_video_feedback_with_large_frame_count(db_session, test_response, video_service):
    """Test saving feedback with very large frame count."""
    large_metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=60000,  # 1 minute
        frame_count=18000,  # 10 min at 30fps
    )

    feedback = await video_service.save_video_feedback(db_session, test_response.id, large_metrics)

    assert feedback.frame_count == 18000
    assert feedback.processing_duration_ms == 60000


# Test: Feedback ID generation
@pytest.mark.asyncio
async def test_save_video_feedback_generates_unique_ids(db_session, test_user, video_service):
    """Test that each feedback gets a unique ID."""
    question = Question(
        content="Question",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    responses = [
        InterviewResponse(
            session_id=interview.id,
            question_id=question.id,
            transcript=f"Answer {i}",
            duration_seconds=100,
        )
        for i in range(3)
    ]
    db_session.add_all(responses)
    await db_session.commit()
    for r in responses:
        await db_session.refresh(r)

    metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )

    feedbacks = []
    for response in responses:
        feedback = await video_service.save_video_feedback(db_session, response.id, metrics)
        feedbacks.append(feedback)

    # All IDs should be unique
    ids = {f.id for f in feedbacks}
    assert len(ids) == 3


# Test: Path conversion from Path to string
@pytest.mark.asyncio
async def test_analyze_video_path_conversion(db_session, test_response, video_service, tmp_path):
    """Test that analyze_video correctly converts Path to string."""
    video_file = tmp_path / "conversion_test.mp4"
    video_file.write_bytes(b"test")

    sample_metrics = VideoMetrics(
        confidence_score=0.75,
        nervousness_score=0.25,
        engagement_score=0.80,
        eye_contact_percentage=0.65,
        looking_away_count=3,
        fidget_count=2,
        hand_gesture_frequency=0.4,
        processing_duration_ms=1500,
        frame_count=30,
    )

    # Mock analyzer to capture the argument
    mock_analyze = AsyncMock(return_value=sample_metrics)

    with patch.object(video_service.analyzer, "analyze", new=mock_analyze):
        await video_service.analyze_video(db_session, test_response.id, str(video_file))

    # Verify analyzer was called with string path
    mock_analyze.assert_called_once()
    call_arg = mock_analyze.call_args[0][0]
    assert isinstance(call_arg, str)
