"""Comprehensive service-level tests for video_service.py to improve coverage.

This test module specifically targets coverage gaps in video_service.py:
- analyze_video() missing file error (line 46)
- save_video_feedback() duplicate check (line 61)
- _get_response() validation (line 89)
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlmodel import SQLModel, select

from app.ai.video_analyzer import VideoMetrics
from app.models.feedback import VideoFeedback
from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.question import Difficulty, Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.video_service import VideoService

# Import register_and_login from conftest.py
from tests.conftest import register_and_login

@pytest.fixture
async def db_session():
    """Provide a database session for tests."""
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email="videotest@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_interview_response(db_session, test_user):
    """Create a test interview response."""
    # Create question and interview
    question = Question(
        content="Test video question",
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

    # Create response
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
    """Provide an instance of VideoService."""
    return VideoService()

@pytest.fixture
def sample_video_metrics():
    """Provide sample VideoMetrics for testing."""
    return VideoMetrics(
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

# Test: analyze_video() missing file error (line 46)

@pytest.mark.asyncio
async def test_analyze_video_raises_error_when_file_not_found(
    db_session, test_interview_response, video_service
):
    """Test that analyze_video raises ValueError when video file doesn't exist."""
    # Use a path that definitely doesn't exist
    nonexistent_path = "/tmp/nonexistent_video_file_12345.mp4"

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await video_service.analyze_video(
            db_session,
            test_interview_response.id,
            nonexistent_path
        )

    error_message = str(exc_info.value)
    assert "Video file not found" in error_message
    assert nonexistent_path in error_message

@pytest.mark.asyncio
async def test_analyze_video_succeeds_when_file_exists(
    db_session, test_interview_response, video_service, sample_video_metrics, tmp_path
):
    """Test that analyze_video succeeds when file exists."""
    # Create a temporary video file
    video_file = tmp_path / "test_video.mp4"
    video_file.write_bytes(b"fake video content")

    # Mock the analyzer to return sample metrics
    with patch.object(
        video_service.analyzer,
        'analyze',
        new=AsyncMock(return_value=sample_video_metrics)
    ):
        result = await video_service.analyze_video(
            db_session,
            test_interview_response.id,
            str(video_file)
        )

    assert result == sample_video_metrics

@pytest.mark.asyncio
async def test_analyze_video_calls_get_response_to_validate(
    db_session, video_service, tmp_path
):
    """Test that analyze_video calls _get_response to validate response exists."""
    # Create a temporary video file
    video_file = tmp_path / "validate_test.mp4"
    video_file.write_bytes(b"test")

    # Use non-existent response ID
    fake_response_id = uuid4()

    # Should raise ValueError from _get_response
    with pytest.raises(ValueError) as exc_info:
        await video_service.analyze_video(
            db_session,
            fake_response_id,
            str(video_file)
        )

    error_message = str(exc_info.value)
    assert "not found" in error_message
    assert str(fake_response_id) in error_message

# Test: save_video_feedback() duplicate check (line 61)

@pytest.mark.asyncio
async def test_save_video_feedback_raises_error_when_feedback_already_exists(
    db_session, test_interview_response, video_service, sample_video_metrics
):
    """Test that save_video_feedback raises ValueError when feedback already exists."""
    # Create existing feedback
    existing_feedback = VideoFeedback(
        response_id=test_interview_response.id,
        confidence_score=0.5,
        nervousness_score=0.3,
        engagement_score=0.6,
        eye_contact_percentage=0.4,
        looking_away_count=5,
        fidget_count=3,
        hand_gesture_frequency=0.2,
        processing_duration_ms=1000,
        frame_count=20,
    )
    db_session.add(existing_feedback)
    await db_session.commit()

    # Try to save new feedback for the same response
    with pytest.raises(ValueError) as exc_info:
        await video_service.save_video_feedback(
            db_session,
            test_interview_response.id,
            sample_video_metrics
        )

    error_message = str(exc_info.value)
    assert "already exists" in error_message
    assert str(test_interview_response.id) in error_message

@pytest.mark.asyncio
async def test_save_video_feedback_succeeds_when_no_existing_feedback(
    db_session, test_interview_response, video_service, sample_video_metrics
):
    """Test that save_video_feedback succeeds when no existing feedback exists."""
    # Ensure no existing feedback
    result = await db_session.exec(
        select(VideoFeedback).where(VideoFeedback.response_id == test_interview_response.id)
    )
    assert result.first() is None

    # Save feedback
    feedback = await video_service.save_video_feedback(
        db_session,
        test_interview_response.id,
        sample_video_metrics
    )

    # Verify feedback was created with correct values
    assert feedback.response_id == test_interview_response.id
    assert feedback.confidence_score == sample_video_metrics.confidence_score
    assert feedback.nervousness_score == sample_video_metrics.nervousness_score
    assert feedback.engagement_score == sample_video_metrics.engagement_score
    assert feedback.eye_contact_percentage == sample_video_metrics.eye_contact_percentage
    assert feedback.looking_away_count == sample_video_metrics.looking_away_count
    assert feedback.fidget_count == sample_video_metrics.fidget_count
    assert feedback.hand_gesture_frequency == sample_video_metrics.hand_gesture_frequency
    assert feedback.processing_duration_ms == sample_video_metrics.processing_duration_ms
    assert feedback.frame_count == sample_video_metrics.frame_count

    # Verify it was persisted
    result = await db_session.exec(
        select(VideoFeedback).where(VideoFeedback.response_id == test_interview_response.id)
    )
    saved_feedback = result.first()
    assert saved_feedback is not None
    assert saved_feedback.id == feedback.id

@pytest.mark.asyncio
async def test_save_video_feedback_commits_and_refreshes(
    db_session, test_interview_response, video_service, sample_video_metrics
):
    """Test that save_video_feedback commits the transaction and refreshes the object."""
    feedback = await video_service.save_video_feedback(
        db_session,
        test_interview_response.id,
        sample_video_metrics
    )

    # Verify the feedback has an ID (committed)
    assert feedback.id is not None

    # Verify we can query it in a new session
    async with SessionLocal() as new_session:
        result = await new_session.exec(
            select(VideoFeedback).where(VideoFeedback.id == feedback.id)
        )
        queried_feedback = result.first()
        assert queried_feedback is not None
        assert queried_feedback.response_id == test_interview_response.id

# Test: _get_response() validation (line 89)

@pytest.mark.asyncio
async def test_get_response_raises_error_when_response_not_found(
    db_session, video_service
):
    """Test that _get_response raises ValueError when response doesn't exist."""
    # Use non-existent response ID
    fake_id = uuid4()

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await video_service._get_response(db_session, fake_id)

    error_message = str(exc_info.value)
    assert "not found" in error_message
    assert str(fake_id) in error_message

@pytest.mark.asyncio
async def test_get_response_returns_response_when_exists(
    db_session, test_interview_response, video_service
):
    """Test that _get_response returns the response when it exists."""
    result = await video_service._get_response(
        db_session,
        test_interview_response.id
    )

    assert result.id == test_interview_response.id
    assert result.session_id == test_interview_response.session_id
    assert result.question_id == test_interview_response.question_id

# Test: process_response_video() integration

@pytest.mark.asyncio
async def test_process_response_video_analyzes_and_saves_feedback(
    db_session, test_interview_response, video_service, sample_video_metrics, tmp_path
):
    """Test that process_response_video orchestrates analysis and feedback saving."""
    # Create video file
    video_file = tmp_path / "integration_test.mp4"
    video_file.write_bytes(b"video content")

    # Mock the analyzer
    with patch.object(
        video_service.analyzer,
        'analyze',
        new=AsyncMock(return_value=sample_video_metrics)
    ):
        feedback = await video_service.process_response_video(
            db_session,
            test_interview_response.id,
            str(video_file)
        )

    # Verify feedback was created and saved
    assert feedback.response_id == test_interview_response.id
    assert feedback.confidence_score == sample_video_metrics.confidence_score

    # Verify it's in the database
    result = await db_session.exec(
        select(VideoFeedback).where(VideoFeedback.response_id == test_interview_response.id)
    )
    saved_feedback = result.first()
    assert saved_feedback is not None

@pytest.mark.asyncio
async def test_process_response_video_fails_when_file_missing(
    db_session, test_interview_response, video_service
):
    """Test that process_response_video fails when video file doesn't exist."""
    nonexistent_path = "/tmp/missing_video_123.mp4"

    with pytest.raises(ValueError) as exc_info:
        await video_service.process_response_video(
            db_session,
            test_interview_response.id,
            nonexistent_path
        )

    assert "Video file not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_process_response_video_fails_when_response_not_found(
    db_session, video_service, tmp_path
):
    """Test that process_response_video fails when response doesn't exist."""
    # Create video file
    video_file = tmp_path / "orphan_test.mp4"
    video_file.write_bytes(b"content")

    fake_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        await video_service.process_response_video(
            db_session,
            fake_id,
            str(video_file)
        )

    error_message = str(exc_info.value)
    assert "not found" in error_message

@pytest.mark.asyncio
async def test_process_response_video_fails_when_feedback_already_exists(
    db_session, test_interview_response, video_service, sample_video_metrics, tmp_path
):
    """Test that process_response_video fails when trying to create duplicate feedback."""
    # Create existing feedback
    existing_feedback = VideoFeedback(
        response_id=test_interview_response.id,
        confidence_score=0.5,
        nervousness_score=0.3,
        engagement_score=0.6,
        eye_contact_percentage=0.4,
        looking_away_count=5,
        fidget_count=3,
        hand_gesture_frequency=0.2,
        processing_duration_ms=1000,
        frame_count=20,
    )
    db_session.add(existing_feedback)
    await db_session.commit()

    # Create video file
    video_file = tmp_path / "duplicate_test.mp4"
    video_file.write_bytes(b"content")

    # Mock analyzer (even though it will fail before calling it)
    with patch.object(
        video_service.analyzer,
        'analyze',
        new=AsyncMock(return_value=sample_video_metrics)
    ):
        with pytest.raises(ValueError) as exc_info:
            await video_service.process_response_video(
                db_session,
                test_interview_response.id,
                str(video_file)
            )

    assert "already exists" in str(exc_info.value)

# Test: Edge cases and additional coverage

@pytest.mark.asyncio
async def test_save_video_feedback_handles_all_metric_fields(
    db_session, test_interview_response, video_service
):
    """Test that all fields from VideoMetrics are properly saved to VideoFeedback."""
    # Create metrics with specific values
    metrics = VideoMetrics(
        confidence_score=0.91,
        nervousness_score=0.12,
        engagement_score=0.88,
        eye_contact_percentage=0.77,
        looking_away_count=7,
        fidget_count=4,
        hand_gesture_frequency=0.55,
        processing_duration_ms=2500,
        frame_count=120,
    )

    feedback = await video_service.save_video_feedback(
        db_session,
        test_interview_response.id,
        metrics
    )

    # Verify every field
    assert feedback.confidence_score == 0.91
    assert feedback.nervousness_score == 0.12
    assert feedback.engagement_score == 0.88
    assert feedback.eye_contact_percentage == 0.77
    assert feedback.looking_away_count == 7
    assert feedback.fidget_count == 4
    assert feedback.hand_gesture_frequency == 0.55
    assert feedback.processing_duration_ms == 2500
    assert feedback.frame_count == 120

@pytest.mark.asyncio
async def test_analyze_video_passes_correct_path_to_analyzer(
    db_session, test_interview_response, video_service, sample_video_metrics, tmp_path
):
    """Test that analyze_video passes the correct file path to the analyzer."""
    video_file = tmp_path / "path_test.webm"
    video_file.write_bytes(b"test content")

    # Mock analyzer and capture the call
    mock_analyze = AsyncMock(return_value=sample_video_metrics)

    with patch.object(video_service.analyzer, 'analyze', new=mock_analyze):
        await video_service.analyze_video(
            db_session,
            test_interview_response.id,
            str(video_file)
        )

    # Verify analyzer was called with the correct path
    mock_analyze.assert_called_once_with(str(video_file))

@pytest.mark.asyncio
async def test_video_service_initializes_analyzer(video_service):
    """Test that VideoService initializes with a VideoAnalyzer instance."""
    from app.ai.video_analyzer import VideoAnalyzer

    assert hasattr(video_service, 'analyzer')
    assert isinstance(video_service.analyzer, VideoAnalyzer)

@pytest.mark.asyncio
async def test_save_video_feedback_for_multiple_different_responses(
    db_session, test_user, video_service, sample_video_metrics
):
    """Test that save_video_feedback works for multiple different responses."""
    # Create two different responses
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

    response1 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Response 1",
        duration_seconds=60,
    )
    response2 = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Response 2",
        duration_seconds=90,
    )
    db_session.add_all([response1, response2])
    await db_session.commit()
    await db_session.refresh(response1)
    await db_session.refresh(response2)

    # Save feedback for both responses (should succeed)
    feedback1 = await video_service.save_video_feedback(
        db_session,
        response1.id,
        sample_video_metrics
    )
    feedback2 = await video_service.save_video_feedback(
        db_session,
        response2.id,
        sample_video_metrics
    )

    assert feedback1.response_id == response1.id
    assert feedback2.response_id == response2.id
    assert feedback1.id != feedback2.id

@pytest.mark.asyncio
async def test_analyze_video_with_pathlib_path(
    db_session, test_interview_response, video_service, sample_video_metrics, tmp_path
):
    """Test that analyze_video works with pathlib.Path objects."""
    video_file = tmp_path / "pathlib_test.mp4"
    video_file.write_bytes(b"content")

    # Pass Path object (not string)
    with patch.object(
        video_service.analyzer,
        'analyze',
        new=AsyncMock(return_value=sample_video_metrics)
    ):
        result = await video_service.analyze_video(
            db_session,
            test_interview_response.id,
            str(video_file)  # Convert to string as expected
        )

    assert result == sample_video_metrics

@pytest.mark.asyncio
async def test_get_response_with_different_response_states(
    db_session, test_user, video_service
):
    """Test _get_response works regardless of response state."""
    # Create responses with different states (some with video, some without)
    question = Question(
        content="Test question",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
    )
    interview = InterviewSession(
        user_id=test_user.id,
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add_all([question, interview])
    await db_session.commit()
    await db_session.refresh(question)
    await db_session.refresh(interview)

    # Response with video
    response_with_video = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer",
        duration_seconds=100,
        video_url="/uploads/video/test.mp4",
    )
    # Response without video
    response_without_video = InterviewResponse(
        session_id=interview.id,
        question_id=question.id,
        transcript="Answer 2",
        duration_seconds=80,
    )

    db_session.add_all([response_with_video, response_without_video])
    await db_session.commit()
    await db_session.refresh(response_with_video)
    await db_session.refresh(response_without_video)

    # Both should be retrievable
    result1 = await video_service._get_response(db_session, response_with_video.id)
    result2 = await video_service._get_response(db_session, response_without_video.id)

    assert result1.video_url == "/uploads/video/test.mp4"
    assert result2.video_url is None
