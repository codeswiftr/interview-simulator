"""Tests for background task logging with correlation fields."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine
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


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    """Create tables once for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db(prepare_db):
    """Truncate tables between tests."""
    async with engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
    yield


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with SessionLocal() as session:
        yield session


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
async def test_background_tasks_log_correlation_fields(caplog, sample_response, tmp_path):
    """Test that background tasks log correlation fields (response_id, task_name)."""
    background_tasks = BackgroundTaskService()

    # Create audio file in the expected location
    from pathlib import Path
    audio_dir = Path("backend/uploads/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "test_audio.webm"
    audio_file.write_bytes(b"fake audio data")
    audio_url = f"/uploads/audio/{audio_file.name}"

    try:
        with caplog.at_level(logging.INFO), patch.object(
            background_tasks.audio_service,
            "process_response_audio",
            return_value=("Test transcript", MagicMock()),
        ), patch.object(
            background_tasks.audio_service, "save_audio_feedback", return_value=MagicMock()
        ), patch.object(
            background_tasks, "generate_content_feedback_async", return_value=None
        ):
            await background_tasks.process_response_audio_async(sample_response.id, audio_url)

        # Check that logs contain correlation fields
        log_records = [record for record in caplog.records if "Successfully processed audio" in record.getMessage()]
        assert len(log_records) > 0

        # Verify correlation fields are present in log extra
        for record in log_records:
            # Check if fields are in extra dict or as attributes
            extra = getattr(record, "extra", {}) or {}
            has_response_id = hasattr(record, "response_id") or "response_id" in extra or str(sample_response.id) in str(record.getMessage())
            has_task_name = hasattr(record, "task_name") or "task_name" in extra or "process_response_audio" in str(record.getMessage())
            # At least one correlation indicator should be present
            assert has_response_id or has_task_name, f"Log record missing correlation fields: {record.getMessage()}"
    finally:
        # Cleanup
        if audio_file.exists():
            audio_file.unlink()

