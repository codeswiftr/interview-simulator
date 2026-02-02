"""Unit tests for AggregationService."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.feedback import AudioFeedback, ContentFeedback, SessionFeedback
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus, ProcessingStatus
from app.models.question import Question
from app.services.aggregation_service import AggregationService
from app.services.scoring_service import ScoringService


@pytest.fixture
def service() -> AggregationService:
    return AggregationService(ScoringService())


def make_content_feedback(**kwargs) -> ContentFeedback:
    defaults = dict(
        response_id=uuid4(),
        technical_accuracy=60,
        star_adherence=60,
        answer_structure=60,
        completeness=60,
        relevance=60,
        overall_content_score=60,
        strengths=[],
        improvements=[],
        detailed_feedback="",
    )
    defaults.update(kwargs)
    return ContentFeedback(**defaults)


def make_audio_feedback(**kwargs) -> AudioFeedback:
    defaults = dict(
        response_id=uuid4(),
        speech_rate_wpm=140,
        speech_rate_score=80,
        filler_words={},
        filler_word_score=80,
        volume_consistency=80,
        confidence_score=80,
        overall_audio_score=80,
    )
    defaults.update(kwargs)
    return AudioFeedback(**defaults)


@pytest.mark.asyncio
async def test_aggregate_session_feedback(service: AggregationService) -> None:
    session = AsyncMock()
    interview_session = InterviewSession(
        user_id=uuid4(),
        interview_type="behavioral",
        question_count=2,
        status=InterviewStatus.COMPLETED,
    )
    interview_session.id = uuid4()

    content_feedbacks = [
        make_content_feedback(
            overall_content_score=80,
            technical_accuracy=65,
            answer_structure=60,
            completeness=60,
            star_adherence=50,
            strengths=["clarity"],
            improvements=["structure"],
        ),
        make_content_feedback(
            overall_content_score=70,
            technical_accuracy=60,
            answer_structure=60,
            completeness=60,
            star_adherence=50,
            strengths=["clarity"],
            improvements=["detail"],
        ),
    ]
    audio_feedbacks = [make_audio_feedback(overall_audio_score=60)]

    result = await service.aggregate_session_feedback(
        session, interview_session, content_feedbacks, audio_feedbacks
    )

    assert isinstance(result, SessionFeedback)
    assert result.session_id == interview_session.id
    assert result.audio_score == 60
    assert result.content_score == 75
    assert result.overall_score == 72.0
    assert result.top_strengths == ["clarity"]
    assert set(result.top_improvements) == {"structure", "detail"}
    assert "Technical accuracy and depth" in result.recommended_practice_areas


def test_aggregate_strengths_and_improvements(service: AggregationService) -> None:
    feedbacks = [
        SimpleNamespace(strengths=["a", "b"], improvements=["x"]),
        SimpleNamespace(strengths=["a"], improvements=["y", "x"]),
    ]
    strengths, improvements = service.aggregate_strengths_and_improvements(feedbacks, top_n=2)

    assert strengths == ["a", "b"]
    assert improvements == ["x", "y"]


def test_determine_practice_areas(service: AggregationService) -> None:
    feedbacks = [
        SimpleNamespace(technical_accuracy=60, answer_structure=65, completeness=68, star_adherence=50),
        SimpleNamespace(technical_accuracy=60, answer_structure=65, completeness=68, star_adherence=50),
    ]
    areas = service.determine_practice_areas(feedbacks, threshold=70)

    assert "Technical accuracy and depth" in areas
    assert "Answer structure and organization" in areas
    assert "Completeness and thoroughness" in areas
    assert "STAR method application" in areas


@pytest.mark.asyncio
async def test_aggregate_user_progress_empty(service: AggregationService) -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    result = await service.aggregate_user_progress(mock_session, uuid4())

    assert result["recommended_practice_areas"] == []
    assert result["average_audio_score"] is None
    assert result["average_content_score"] is None


@pytest.mark.asyncio
async def test_aggregate_user_progress_with_feedbacks(service: AggregationService) -> None:
    user_id = uuid4()
    session1 = InterviewSession(
        user_id=user_id,
        interview_type="behavioral",
        question_count=1,
        status=InterviewStatus.COMPLETED,
    )
    session1.id = uuid4()
    session2 = InterviewSession(
        user_id=user_id,
        interview_type="behavioral",
        question_count=1,
        status=InterviewStatus.ANALYZED,
    )
    session2.id = uuid4()

    feedback1 = SessionFeedback(
        session_id=session1.id,
        overall_score=80,
        audio_score=60,
        content_score=90,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=["A"],
        next_question_ids=[],
    )
    feedback2 = SessionFeedback(
        session_id=session2.id,
        overall_score=70,
        audio_score=80,
        content_score=70,
        top_strengths=[],
        top_improvements=[],
        recommended_practice_areas=["A", "B"],
        next_question_ids=[],
    )

    mock_session = AsyncMock()
    mock_result_sessions = MagicMock()
    mock_result_sessions.all.return_value = [session1, session2]
    mock_result_feedbacks = MagicMock()
    mock_result_feedbacks.all.return_value = [feedback1, feedback2]
    mock_session.exec.side_effect = [mock_result_sessions, mock_result_feedbacks]

    result = await service.aggregate_user_progress(mock_session, user_id)

    assert result["average_audio_score"] == 70.0
    assert result["average_content_score"] == 80.0
    assert result["recommended_practice_areas"] == ["A", "B"]


@pytest.mark.asyncio
async def test_aggregate_user_improvements_insufficient_sessions(service: AggregationService) -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        InterviewSession(
            user_id=uuid4(),
            interview_type="behavioral",
            question_count=1,
            status=InterviewStatus.COMPLETED,
        )
    ]
    mock_session.exec.return_value = mock_result

    result = await service.aggregate_user_improvements(mock_session, uuid4())

    assert result["data_available"] is False
    assert result["sessions_analyzed"] == 1


@pytest.mark.asyncio
async def test_aggregate_user_improvements_delivery_behavioral(service: AggregationService) -> None:
    user_id = uuid4()
    session_recent = InterviewSession(
        user_id=user_id,
        interview_type="behavioral",
        question_count=1,
        status=InterviewStatus.COMPLETED,
    )
    session_recent.id = uuid4()
    session_prev = InterviewSession(
        user_id=user_id,
        interview_type="behavioral",
        question_count=1,
        status=InterviewStatus.ANALYZED,
    )
    session_prev.id = uuid4()
    filler_sessions = [
        InterviewSession(
            user_id=user_id,
            interview_type="behavioral",
            question_count=1,
            status=InterviewStatus.COMPLETED,
        )
        for _ in range(4)
    ]
    for s in filler_sessions:
        s.id = uuid4()

    response_recent = InterviewResponse(
        session_id=session_recent.id,
        question_id=uuid4(),
    )
    response_recent.id = uuid4()
    response_prev = InterviewResponse(
        session_id=session_prev.id,
        question_id=uuid4(),
    )
    response_prev.id = uuid4()

    question_behavioral = Question(content="Q", category="behavioral", difficulty="easy", is_active=True)

    content_recent = make_content_feedback(
        response_id=response_recent.id,
        star_adherence=80,
        answer_structure=80,
        completeness=80,
    )
    content_prev = make_content_feedback(
        response_id=response_prev.id,
        star_adherence=60,
        answer_structure=60,
        completeness=60,
    )

    audio_recent = make_audio_feedback(response_id=response_recent.id, filler_word_score=90)
    audio_prev = make_audio_feedback(response_id=response_prev.id, filler_word_score=50)

    mock_session = AsyncMock()
    mock_result_sessions = MagicMock()
    mock_result_sessions.all.return_value = [
        session_recent,
        *filler_sessions,
        session_prev,
    ]

    mock_result_responses = MagicMock()
    mock_result_responses.all.return_value = [
        (response_recent, question_behavioral),
        (response_prev, question_behavioral),
    ]

    mock_result_content = MagicMock()
    mock_result_content.all.return_value = [content_recent, content_prev]

    mock_result_audio = MagicMock()
    mock_result_audio.all.return_value = [audio_recent, audio_prev]

    mock_session.exec.side_effect = [
        mock_result_sessions,
        mock_result_responses,
        mock_result_content,
        mock_result_audio,
    ]

    result = await service.aggregate_user_improvements(mock_session, user_id)

    assert result["data_available"] is True
    assert result["delivery"]["trend"] == "improving"
    assert result["behavioral"]["trend"] == "improving"


@pytest.mark.asyncio
async def test_aggregate_skills_gap_basic(service: AggregationService) -> None:
    user_id = uuid4()
    session_recent = InterviewSession(
        user_id=user_id,
        interview_type="behavioral",
        question_count=1,
        status=InterviewStatus.COMPLETED,
        created_at=datetime.now(UTC),
    )
    session_recent.id = uuid4()
    session_prev = InterviewSession(
        user_id=user_id,
        interview_type="behavioral",
        question_count=1,
        status=InterviewStatus.ANALYZED,
        created_at=datetime.now(UTC),
    )
    session_prev.id = uuid4()

    response_recent = InterviewResponse(
        session_id=session_recent.id,
        question_id=uuid4(),
    )
    response_recent.id = uuid4()
    response_prev = InterviewResponse(
        session_id=session_prev.id,
        question_id=uuid4(),
    )
    response_prev.id = uuid4()

    question_behavioral = Question(content="Q", category="behavioral", difficulty="easy", is_active=True)

    content_recent = make_content_feedback(
        response_id=response_recent.id,
        overall_content_score=80,
        star_adherence=80,
        answer_structure=80,
        completeness=80,
        relevance=80,
    )
    content_prev = make_content_feedback(
        response_id=response_prev.id,
        overall_content_score=70,
        star_adherence=70,
        answer_structure=70,
        completeness=70,
        relevance=70,
    )

    audio_recent = make_audio_feedback(response_id=response_recent.id, overall_audio_score=85)
    audio_prev = make_audio_feedback(response_id=response_prev.id, overall_audio_score=75)

    mock_session = AsyncMock()
    mock_result_sessions = MagicMock()
    mock_result_sessions.all.return_value = [session_recent, session_prev]

    mock_result_responses = MagicMock()
    mock_result_responses.all.return_value = [
        (response_recent, question_behavioral),
        (response_prev, question_behavioral),
    ]

    mock_result_content = MagicMock()
    mock_result_content.all.return_value = [content_recent, content_prev]

    mock_result_audio = MagicMock()
    mock_result_audio.all.return_value = [audio_recent, audio_prev]

    mock_session.exec.side_effect = [
        mock_result_sessions,
        mock_result_responses,
        mock_result_content,
        mock_result_audio,
    ]

    result = await service.aggregate_skills_gap(mock_session, user_id)

    names = {d.name for d in result.dimensions}
    assert "Content" in names
    assert "Delivery" in names
    assert "Behavioral" in names


@pytest.mark.asyncio
async def test_aggregate_processing_status(service: AggregationService) -> None:
    session_id = uuid4()
    response1 = InterviewResponse(session_id=session_id, question_id=uuid4())
    response1.processing_status = ProcessingStatus.TRANSCRIBING
    response2 = InterviewResponse(session_id=session_id, question_id=uuid4())
    response2.processing_status = ProcessingStatus.COMPLETED

    mock_session = AsyncMock()
    mock_result_responses = MagicMock()
    mock_result_responses.all.return_value = [response1, response2]

    mock_result_feedback = MagicMock()
    mock_result_feedback.first.return_value = None

    mock_session.exec.side_effect = [mock_result_responses, mock_result_feedback]

    result = await service.aggregate_processing_status(mock_session, session_id)

    assert result["status_counts"]["transcribing"] == 1
    assert result["status_counts"]["completed"] == 1
    assert result["current_step"] == "transcribing"
