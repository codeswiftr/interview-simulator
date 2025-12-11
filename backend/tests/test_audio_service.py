"""Tests for audio processing service."""

from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

from app.ai.audio_analyzer import AudioMetrics
from app.ai.transcriber import TranscriptionResult
from app.db import SessionLocal, engine
from app.models.feedback import AudioFeedback
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus, InterviewType
from app.models.question import Question, QuestionCategory
from app.models.user import User
from app.security import hash_password
from app.services.audio_service import AudioService


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
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def sample_question(db_session):
    """Create a test question."""
    question = Question(
        content="Tell me about yourself",
        category=QuestionCategory.BEHAVIORAL,
        expected_duration_seconds=180,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def sample_response(db_session, sample_interview_session, sample_question):
    """Create a test interview response."""
    response = InterviewResponse(
        session_id=sample_interview_session.id,
        question_id=sample_question.id,
        audio_url="/uploads/audio/test.webm",
        duration_seconds=120,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)
    return response


@pytest.fixture
def mock_audio_file(tmp_path):
    """Create a mock audio file for testing."""
    audio_file = tmp_path / "test_audio.webm"
    audio_file.write_bytes(b"fake audio data")
    return str(audio_file)


@pytest.fixture
def audio_service():
    """Create an AudioService instance."""
    return AudioService()


class TestAudioService:
    """Test suite for AudioService."""

    @pytest.mark.asyncio
    async def test_process_response_audio_updates_transcript(
        self, audio_service, db_session, sample_response, mock_audio_file
    ):
        """Test that processing audio updates the response transcript."""
        # Mock transcription
        mock_transcript = TranscriptionResult(
            text="This is a test transcript",
            duration_seconds=120.0,
            language="en",
        )

        with patch.object(
            audio_service.transcriber, "transcribe", return_value=mock_transcript
        ), patch.object(
            audio_service.analyzer,
            "analyze",
            return_value=AudioMetrics(
                speech_rate_wpm=130.0,
                filler_words={"um": 2},
                volume_consistency=85.0,
                confidence_score=75.0,
            ),
        ):
            transcript, metrics = await audio_service.process_response_audio(
                db_session, sample_response.id, mock_audio_file
            )

            await db_session.refresh(sample_response)
            assert sample_response.transcript == "This is a test transcript"
            assert sample_response.word_count == 5
            assert sample_response.duration_seconds == 120

    @pytest.mark.asyncio
    async def test_process_response_audio_creates_audio_feedback(
        self, audio_service, db_session, sample_response, sample_question, mock_audio_file
    ):
        """Test that processing audio creates AudioFeedback record."""
        # Set up response with transcript
        sample_response.transcript = "This is a test transcript with some words"
        sample_response.word_count = 7
        await db_session.commit()

        mock_transcript = TranscriptionResult(
            text="This is a test transcript with some words",
            duration_seconds=120.0,
        )

        mock_metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={"um": 2},
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        with patch.object(
            audio_service.transcriber, "transcribe", return_value=mock_transcript
        ), patch.object(audio_service.analyzer, "analyze", return_value=mock_metrics):
            await audio_service.process_response_audio(
                db_session, sample_response.id, mock_audio_file
            )

            # Save audio feedback
            await audio_service.save_audio_feedback(db_session, sample_response.id, mock_metrics)

            # Verify AudioFeedback was created
            from sqlmodel import select

            result = await db_session.exec(
                select(AudioFeedback).where(AudioFeedback.response_id == sample_response.id)
            )
            feedback = result.first()
            assert feedback is not None
            assert feedback.speech_rate_wpm == 130.0
            assert feedback.filler_words == {"um": 2}
            assert feedback.overall_audio_score > 0

    @pytest.mark.asyncio
    async def test_process_response_audio_handles_transcription_failure(
        self, audio_service, db_session, sample_response, mock_audio_file
    ):
        """Test that transcription failures are handled gracefully."""
        with patch.object(
            audio_service.transcriber, "transcribe", side_effect=ValueError("Transcription failed")
        ), pytest.raises(ValueError, match="Failed to process audio"):
            await audio_service.process_response_audio(
                db_session, sample_response.id, mock_audio_file
            )

    @pytest.mark.asyncio
    async def test_process_response_audio_handles_analysis_failure(
        self, audio_service, db_session, sample_response, mock_audio_file
    ):
        """Test that analysis failures are handled gracefully."""
        mock_transcript = TranscriptionResult(text="Test transcript", duration_seconds=120.0)

        with patch.object(
            audio_service.transcriber, "transcribe", return_value=mock_transcript
        ), patch.object(
            audio_service.analyzer, "analyze", side_effect=ValueError("Analysis failed")
        ), pytest.raises(ValueError, match="Failed to process audio"):
            await audio_service.process_response_audio(
                db_session, sample_response.id, mock_audio_file
            )

    @pytest.mark.asyncio
    async def test_save_audio_feedback_calculates_scores(
        self, audio_service, db_session, sample_response, sample_question
    ):
        """Test that audio feedback scores are calculated correctly."""
        # Set up response with realistic word count
        sample_response.transcript = "This is a test transcript with enough words"
        sample_response.word_count = 100  # 1 filler in 100 words = 1% filler rate
        await db_session.commit()

        metrics = AudioMetrics(
            speech_rate_wpm=130.0,  # Within optimal range
            filler_words={"um": 1},  # Low filler count
            volume_consistency=90.0,
            confidence_score=80.0,
        )

        feedback = await audio_service.save_audio_feedback(
            db_session, sample_response.id, metrics
        )

        assert feedback.speech_rate_score == 100.0  # Optimal range
        assert feedback.filler_word_score > 0
        assert feedback.overall_audio_score > 0
        assert feedback.overall_audio_score <= 100

    @pytest.mark.asyncio
    async def test_save_audio_feedback_prevents_duplicates(
        self, audio_service, db_session, sample_response
    ):
        """Test that duplicate audio feedback is prevented."""
        metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={},
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        # Create first feedback
        await audio_service.save_audio_feedback(db_session, sample_response.id, metrics)

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await audio_service.save_audio_feedback(db_session, sample_response.id, metrics)

