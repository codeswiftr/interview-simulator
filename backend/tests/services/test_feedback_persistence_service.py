"""Unit tests for FeedbackPersistenceService."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.feedback import AudioFeedback, ContentFeedback, SessionFeedback, VideoFeedback
from app.services.feedback_persistence_service import FeedbackPersistenceService


@pytest.fixture
def service() -> FeedbackPersistenceService:
    return FeedbackPersistenceService()


@pytest.mark.asyncio
async def test_get_by_response_id(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    feedback = ContentFeedback(
        response_id=response_id,
        technical_accuracy=80,
        star_adherence=70,
        answer_structure=75,
        completeness=65,
        relevance=60,
        overall_content_score=72,
        strengths=["clear"],
        improvements=["detail"],
        detailed_feedback="ok",
    )
    mock_result.first.return_value = feedback
    mock_session.exec.return_value = mock_result

    result = await service.get_by_response_id(mock_session, response_id)

    assert result == feedback


@pytest.mark.asyncio
async def test_get_all_by_session_id(service: FeedbackPersistenceService) -> None:
    session_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    feedbacks = [
        ContentFeedback(
            response_id=uuid4(),
            technical_accuracy=80,
            star_adherence=70,
            answer_structure=75,
            completeness=65,
            relevance=60,
            overall_content_score=72,
            strengths=[],
            improvements=[],
            detailed_feedback="",
        ),
        ContentFeedback(
            response_id=uuid4(),
            technical_accuracy=90,
            star_adherence=80,
            answer_structure=85,
            completeness=75,
            relevance=70,
            overall_content_score=82,
            strengths=[],
            improvements=[],
            detailed_feedback="",
        ),
    ]
    mock_result.all.return_value = feedbacks
    mock_session.exec.return_value = mock_result

    result = await service.get_all_by_session_id(mock_session, session_id)

    assert result == feedbacks


@pytest.mark.asyncio
async def test_create_content_feedback(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    metrics = SimpleNamespace(
        technical_accuracy=80,
        star_adherence=70,
        answer_structure=75,
        completeness=65,
        relevance=60,
        overall_content_score=72,
        strengths=["clear"],
        improvements=["detail"],
        detailed_feedback="ok",
    )

    feedback = await service.create_content_feedback(mock_session, response_id, metrics)

    assert feedback.response_id == response_id
    assert feedback.overall_content_score == 72
    assert feedback.strengths == ["clear"]
    assert feedback.improvements == ["detail"]
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_create_content_feedback_with_dict(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    metrics = {
        "technical_accuracy": 85,
        "star_adherence": 75,
        "answer_structure": 70,
        "completeness": 65,
        "relevance": 60,
        "overall_content_score": 74,
        "strengths": ["structure"],
        "improvements": ["examples"],
        "detailed_feedback": "solid",
    }

    feedback = await service.create_content_feedback(mock_session, response_id, metrics)

    assert feedback.overall_content_score == 74
    assert feedback.strengths == ["structure"]
    assert feedback.improvements == ["examples"]


@pytest.mark.asyncio
async def test_exists_for_response_true(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = ContentFeedback(
        response_id=response_id,
        technical_accuracy=80,
        star_adherence=70,
        answer_structure=75,
        completeness=65,
        relevance=60,
        overall_content_score=72,
        strengths=[],
        improvements=[],
        detailed_feedback="",
    )
    mock_session.exec.return_value = mock_result

    assert await service.exists_for_response(mock_session, response_id) is True


@pytest.mark.asyncio
async def test_exists_for_response_false(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    assert await service.exists_for_response(mock_session, response_id) is False


@pytest.mark.asyncio
async def test_get_by_session_id(service: FeedbackPersistenceService) -> None:
    session_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    feedback = SessionFeedback(
        session_id=session_id,
        overall_score=80,
        audio_score=70,
        content_score=85,
        top_strengths=["clarity"],
        top_improvements=["structure"],
        recommended_practice_areas=["completeness"],
        next_question_ids=["q1"],
    )
    mock_result.first.return_value = feedback
    mock_session.exec.return_value = mock_result

    result = await service.get_by_session_id(mock_session, session_id)

    assert result == feedback


@pytest.mark.asyncio
async def test_create_session_feedback(service: FeedbackPersistenceService) -> None:
    session_id = uuid4()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    feedback = await service.create_session_feedback(
        mock_session,
        session_id=session_id,
        overall_score=82,
        audio_score=70,
        content_score=85,
        top_strengths=["clarity"],
        top_improvements=["structure"],
        recommended_practice_areas=["completeness"],
        next_question_ids=["q1"],
    )

    assert feedback.session_id == session_id
    assert feedback.overall_score == 82
    assert feedback.next_question_ids == ["q1"]
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_exists_for_session_true(service: FeedbackPersistenceService) -> None:
    session_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = SessionFeedback(
        session_id=session_id,
        overall_score=80,
        audio_score=70,
        content_score=85,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=[],
        next_question_ids=[],
    )
    mock_session.exec.return_value = mock_result

    assert await service.exists_for_session(mock_session, session_id) is True


@pytest.mark.asyncio
async def test_exists_for_session_false(service: FeedbackPersistenceService) -> None:
    session_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    assert await service.exists_for_session(mock_session, session_id) is False


@pytest.mark.asyncio
async def test_get_video_by_response_id(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    feedback = VideoFeedback(
        response_id=response_id,
        confidence_score=0.7,
        nervousness_score=0.2,
        engagement_score=0.8,
        eye_contact_percentage=0.6,
        looking_away_count=1,
        processing_duration_ms=1000,
        frame_count=100,
    )
    mock_result.first.return_value = feedback
    mock_session.exec.return_value = mock_result

    result = await service.get_video_by_response_id(mock_session, response_id)

    assert result == feedback


@pytest.mark.asyncio
async def test_get_audio_by_response_id(service: FeedbackPersistenceService) -> None:
    response_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    feedback = AudioFeedback(
        response_id=response_id,
        speech_rate_wpm=140,
        speech_rate_score=85,
        filler_words={"um": 2},
        filler_word_score=80,
        volume_consistency=75,
        confidence_score=78,
        overall_audio_score=80,
    )
    mock_result.first.return_value = feedback
    mock_session.exec.return_value = mock_result

    result = await service.get_audio_by_response_id(mock_session, response_id)

    assert result == feedback


@pytest.mark.asyncio
async def test_get_audio_by_session_id(service: FeedbackPersistenceService) -> None:
    session_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    feedbacks = [
        AudioFeedback(
            response_id=uuid4(),
            speech_rate_wpm=140,
            speech_rate_score=85,
            filler_words={},
            filler_word_score=80,
            volume_consistency=75,
            confidence_score=78,
            overall_audio_score=80,
        )
    ]
    mock_result.all.return_value = feedbacks
    mock_session.exec.return_value = mock_result

    result = await service.get_audio_by_session_id(mock_session, session_id)

    assert result == feedbacks
