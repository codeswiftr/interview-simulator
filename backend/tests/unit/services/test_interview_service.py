"""Unit tests for InterviewService (unit/services location)."""

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.interview_service import InterviewService
from app.models.interview import InterviewSession, InterviewType
from app.models.question import Question


@pytest.fixture
def service() -> InterviewService:
    return InterviewService()


@pytest.mark.asyncio
async def test_get_category_for_type(service: InterviewService) -> None:
    assert service._get_category_for_type(InterviewType.BEHAVIORAL) is not None
    assert service._get_category_for_type(InterviewType.TECHNICAL) is not None
    assert service._get_category_for_type(InterviewType.SYSTEM_DESIGN) is not None
    assert service._get_category_for_type(InterviewType.MIXED) is None


@pytest.mark.asyncio
async def test_assign_questions_general_pool_success(service: InterviewService) -> None:
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    mock_interview = MagicMock(spec=InterviewSession)
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.BEHAVIORAL
    mock_interview.question_count = 2
    mock_interview.difficulty = "easy"
    mock_interview.target_company = None

    q1 = Question(id=uuid4(), expected_duration_seconds=120)
    q2 = Question(id=uuid4(), expected_duration_seconds=180)
    mock_result = MagicMock()
    mock_result.all.return_value = [q1, q2]
    mock_session.exec.return_value = mock_result

    result = await service.assign_questions(mock_session, mock_interview)

    assert len(result) == 2
    assert result[0].question_id == q1.id
    assert result[1].question_id == q2.id
    assert result[0].time_limit_seconds == 120
    assert result[1].time_limit_seconds == 180


@pytest.mark.asyncio
async def test_assign_questions_company_then_general(service: InterviewService) -> None:
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    mock_interview = MagicMock(spec=InterviewSession)
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.TECHNICAL
    mock_interview.question_count = 2
    mock_interview.difficulty = "medium"
    mock_interview.target_company = "Google"

    q1 = Question(id=uuid4(), expected_duration_seconds=150)
    q2 = Question(id=uuid4(), expected_duration_seconds=150)

    mock_result_company = MagicMock()
    mock_result_company.all.return_value = [q1]
    mock_result_general = MagicMock()
    mock_result_general.all.return_value = [q2]

    mock_session.exec.side_effect = [mock_result_company, mock_result_general]

    result = await service.assign_questions(mock_session, mock_interview)

    assert [r.question_id for r in result] == [q1.id, q2.id]


@pytest.mark.asyncio
async def test_assign_questions_insufficient_raises(service: InterviewService) -> None:
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    mock_interview = MagicMock(spec=InterviewSession)
    mock_interview.id = uuid4()
    mock_interview.interview_type = InterviewType.SYSTEM_DESIGN
    mock_interview.question_count = 3
    mock_interview.difficulty = "hard"
    mock_interview.target_company = None

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    with pytest.raises(ValueError, match="Not enough questions available"):
        await service.assign_questions(mock_session, mock_interview)


@pytest.mark.asyncio
async def test_get_interview_questions(service: InterviewService) -> None:
    mock_session = AsyncMock()
    interview_id = uuid4()

    q1 = Question(id=uuid4())
    mock_result = MagicMock()
    mock_result.all.return_value = [q1]
    mock_session.exec.return_value = mock_result

    result = await service.get_interview_questions(mock_session, interview_id)

    assert len(result) == 1
    assert result[0].id == q1.id


@pytest.mark.asyncio
async def test_has_assigned_questions_true_false(service: InterviewService) -> None:
    mock_session = AsyncMock()
    interview_id = uuid4()

    mock_result = MagicMock()
    mock_result.one.return_value = 1
    mock_session.exec.return_value = mock_result

    assert await service.has_assigned_questions(mock_session, interview_id) is True

    mock_result.one.return_value = 0
    assert await service.has_assigned_questions(mock_session, interview_id) is False


@pytest.mark.asyncio
async def test_assign_specific_question_success(service: InterviewService) -> None:
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    interview = MagicMock(spec=InterviewSession)
    interview.id = uuid4()
    question_id = uuid4()

    question = Question(id=question_id, expected_duration_seconds=200)
    mock_result = MagicMock()
    mock_result.first.return_value = question
    mock_session.exec.return_value = mock_result

    result = await service.assign_specific_question(mock_session, interview, question_id)

    assert result.question_id == question_id
    assert result.session_id == interview.id
    assert result.time_limit_seconds == 200


@pytest.mark.asyncio
async def test_assign_specific_question_not_found(service: InterviewService) -> None:
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    interview = MagicMock(spec=InterviewSession)
    interview.id = uuid4()
    question_id = uuid4()

    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(ValueError, match="Question not found"):
        await service.assign_specific_question(mock_session, interview, question_id)
