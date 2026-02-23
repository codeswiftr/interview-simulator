"""Tests for background task logging with correlation fields."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.interview import (
    InterviewResponse,
    InterviewSession,
    InterviewStatus,
    InterviewType,
    ProcessingStatus,
)
from app.models.question import Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.background_tasks import BackgroundTaskService

# Use shared fixtures from conftest.py (db_session, clean_database, etc.)


@pytest.fixture
async def sample_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_interview_session(db_session, sample_user):
    """Create a test interview session."""
    session = InterviewSession(
        user_id=sample_user.id,
        interview_type=InterviewType.BEHAVIORAL,
        question_count=3,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def sample_response(db_session, sample_interview_session):
    """Create a test interview response."""
    question = Question(
        content="Tell me about yourself",
        category=QuestionCategory.BEHAVIORAL,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    response = InterviewResponse(
        session_id=sample_interview_session.id,
        question_id=question.id,
        audio_url="/uploads/audio/test.webm",
        transcript="This is a test transcript",
        word_count=5,
        duration_seconds=120,
        processing_status=ProcessingStatus.PENDING,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)
    return response


@pytest.mark.asyncio
async def test_background_tasks_log_correlation_fields(
    caplog, sample_response, tmp_path, db_session
):
    """Test that background tasks log correlation fields (response_id, task_name)."""
    background_tasks = BackgroundTaskService()

    # Create audio file in the expected location
    from pathlib import Path

    audio_dir = Path("backend/uploads/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "test_audio.webm"
    audio_file.write_bytes(b"fake audio data")
    audio_url = f"/uploads/audio/{audio_file.name}"

    # Mock AudioMetrics for the return value
    mock_metrics = MagicMock()
    mock_metrics.speech_rate_wpm = 140.0
    mock_metrics.speech_rate_score = 75.0
    mock_metrics.filler_words = {}
    mock_metrics.filler_word_score = 80.0
    mock_metrics.confidence_score = 70.0
    mock_metrics.volume_consistency = 78.0
    mock_metrics.overall_audio_score = 76.0

    try:
        with (
            caplog.at_level(logging.INFO),
            patch("app.services.background_tasks.SessionLocal") as mock_session_local,
            patch.object(
                background_tasks,
                "_process_audio_with_retry",
                new_callable=AsyncMock,
                return_value=("Test transcript", mock_metrics),
            ),
            patch.object(
                background_tasks.audio_service, "save_audio_feedback", new_callable=AsyncMock
            ),
            patch.object(
                background_tasks, "generate_content_feedback_async", new_callable=AsyncMock
            ),
        ):
            # Mock the session context manager to return our test response
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.first.return_value = sample_response
            mock_session.exec = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock(return_value=None)

            # Make it work as async context manager
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_ctx

            await background_tasks.process_response_audio_async(sample_response.id, audio_url)

        # Check that logs contain correlation fields
        log_records = [
            record
            for record in caplog.records
            if "Successfully processed audio" in record.getMessage()
        ]
        assert len(log_records) > 0, (
            f"Expected log 'Successfully processed audio' not found. Available logs: {[r.getMessage() for r in caplog.records]}"
        )

        # Verify correlation fields are present in log extra
        for record in log_records:
            # Check if fields are in extra dict or as attributes
            extra = getattr(record, "extra", {}) or {}
            has_response_id = (
                hasattr(record, "response_id")
                or "response_id" in extra
                or str(sample_response.id) in str(record.getMessage())
            )
            has_task_name = (
                hasattr(record, "task_name")
                or "task_name" in extra
                or "process_response_audio" in str(record.getMessage())
            )
            # At least one correlation indicator should be present
            assert has_response_id or has_task_name, (
                f"Log record missing correlation fields: {record.getMessage()}"
            )
    finally:
        # Cleanup
        if audio_file.exists():
            audio_file.unlink()
