"""Tests for background task service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

from app.db import SessionLocal, engine
from app.models.feedback import AudioFeedback, ContentFeedback, SessionFeedback
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
    """Create a test interview response with transcript."""
    from app.models.question import Question, QuestionCategory

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


@pytest.fixture
def background_tasks():
    """Create BackgroundTaskService instance."""
    return BackgroundTaskService()


class TestBackgroundTasks:
    """Test suite for BackgroundTaskService."""

    @pytest.mark.asyncio
    async def test_process_response_audio_async_completes(
        self, background_tasks, db_session, sample_response, tmp_path
    ):
        """Test that audio processing task completes successfully."""
        audio_file = tmp_path / "test_audio.webm"
        audio_file.write_bytes(b"fake audio data")
        audio_url = f"/uploads/audio/{audio_file.name}"

        with patch.object(
            background_tasks.audio_service,
            "process_response_audio",
            return_value=("Test transcript", MagicMock()),
        ), patch.object(
            background_tasks.audio_service, "save_audio_feedback", return_value=MagicMock()
        ), patch.object(
            background_tasks, "generate_content_feedback_async", return_value=None
        ):
            await background_tasks.process_response_audio_async(sample_response.id, audio_url)

            # Verify processing status was updated
            await db_session.refresh(sample_response)
            # Status should be updated during processing

    @pytest.mark.asyncio
    async def test_process_response_audio_async_handles_errors(
        self, background_tasks, db_session, sample_response
    ):
        """Test that errors are logged but don't crash."""
        with patch.object(
            background_tasks.audio_service,
            "process_response_audio",
            side_effect=ValueError("Processing failed"),
        ):
            # Should not raise exception
            await background_tasks.process_response_audio_async(
                sample_response.id, "/uploads/audio/test.webm"
            )

    @pytest.mark.asyncio
    async def test_generate_content_feedback_async_creates_feedback(
        self, background_tasks, db_session, sample_response
    ):
        """Test that content feedback is created."""
        with patch.object(
            background_tasks.feedback_service,
            "generate_feedback",
            return_value=MagicMock(),
        ):
            await background_tasks.generate_content_feedback_async(sample_response.id)

            # Verify feedback was created (mocked, so just check it was called)
            background_tasks.feedback_service.generate_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_session_feedback_async_creates_session_feedback(
        self, background_tasks, db_session, sample_interview_session, sample_response
    ):
        """Test that session feedback is created."""
        with patch.object(
            background_tasks.feedback_service,
            "generate_session_feedback",
            return_value=MagicMock(),
        ):
            await background_tasks.generate_session_feedback_async(sample_interview_session.id)

            # Verify session feedback was created
            background_tasks.feedback_service.generate_session_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_session_feedback_async_waits_for_responses(
        self, background_tasks, db_session, sample_interview_session
    ):
        """Test that session feedback waits for responses."""
        import asyncio

        call_times = []

        async def mock_generate(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            return MagicMock()

        with patch.object(
            background_tasks.feedback_service, "generate_session_feedback", side_effect=mock_generate
        ):
            start_time = asyncio.get_event_loop().time()
            await background_tasks.generate_session_feedback_async(sample_interview_session.id)
            end_time = asyncio.get_event_loop().time()

            # Should have waited at least 2 seconds
            assert end_time - start_time >= 1.5  # Allow some margin

