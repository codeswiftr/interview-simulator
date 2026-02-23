"""Pure unit tests for questions API routes.

Tests list, random, get-by-id, and create question endpoints.
No database required — AsyncSession is fully mocked.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.questions import (
    create_question,
    get_question,
    get_random_question,
    list_questions,
)
from app.models.question import (
    Difficulty,
    Industry,
    QuestionCategory,
    QuestionCreate,
    Role,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_session():
    session = AsyncMock()
    result = MagicMock()
    session.exec = AsyncMock(return_value=result)
    return session, result


def _make_question(question_id=None):
    q = MagicMock()
    q.id = question_id or uuid4()
    q.content = "Describe a time you handled conflict on a team."
    q.category = QuestionCategory.BEHAVIORAL
    q.difficulty = Difficulty.MEDIUM
    q.industry = Industry.GENERAL
    q.role = Role.GENERAL
    q.company_tags = []
    q.topic_tags = []
    q.expected_duration_seconds = 180
    q.is_active = True
    return q


def _make_question_create():
    return QuestionCreate(
        content="Explain the CAP theorem.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        industry=Industry.SAAS,
        role=Role.SOFTWARE_ENGINEER,
    )


def _make_user():
    user = MagicMock()
    user.id = uuid4()
    return user


# ---------------------------------------------------------------------------
# list_questions
# ---------------------------------------------------------------------------


class TestListQuestions:
    # NOTE: list_questions uses FastAPI Query() objects as defaults for limit/offset.
    # When calling the handler directly (bypassing FastAPI dependency injection) we
    # must supply plain integer values for limit and offset so that SQLAlchemy can
    # pass them through to the underlying SQL statement.

    @pytest.mark.asyncio
    async def test_returns_all_active_questions(self):
        session, result = _mock_session()
        questions = [_make_question(), _make_question()]
        result.all.return_value = questions

        found = await list_questions(limit=20, offset=0, session=session)
        assert found == questions
        session.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none(self):
        session, result = _mock_session()
        result.all.return_value = []

        found = await list_questions(limit=20, offset=0, session=session)
        assert found == []

    @pytest.mark.asyncio
    async def test_accepts_category_filter(self):
        session, result = _mock_session()
        question = _make_question()
        result.all.return_value = [question]

        found = await list_questions(
            category=QuestionCategory.BEHAVIORAL,
            limit=20,
            offset=0,
            session=session,
        )
        assert len(found) == 1

    @pytest.mark.asyncio
    async def test_accepts_difficulty_filter(self):
        session, result = _mock_session()
        question = _make_question()
        result.all.return_value = [question]

        found = await list_questions(
            difficulty=Difficulty.EASY,
            limit=20,
            offset=0,
            session=session,
        )
        assert len(found) == 1

    @pytest.mark.asyncio
    async def test_accepts_company_and_topic_filters(self):
        session, result = _mock_session()
        question = _make_question()
        result.all.return_value = [question]

        found = await list_questions(
            company="Google",
            topic="leadership",
            limit=20,
            offset=0,
            session=session,
        )
        assert len(found) == 1


# ---------------------------------------------------------------------------
# get_random_question
# ---------------------------------------------------------------------------


class TestGetRandomQuestion:
    # NOTE: exclude_ids uses Query(None, ...) as a default. Pass explicit None
    # to avoid the Query sentinel being interpreted as the actual value.

    @pytest.mark.asyncio
    async def test_returns_random_question(self):
        session, result = _mock_session()
        question = _make_question()
        result.first.return_value = question

        found = await get_random_question(exclude_ids=None, session=session)
        assert found == question

    @pytest.mark.asyncio
    async def test_raises_404_when_no_matching_question(self):
        session, result = _mock_session()
        result.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_random_question(exclude_ids=None, session=session)
        assert exc_info.value.status_code == 404
        assert "No matching question found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_accepts_exclude_ids(self):
        session, result = _mock_session()
        question = _make_question()
        result.first.return_value = question

        found = await get_random_question(
            exclude_ids=[uuid4(), uuid4()],
            session=session,
        )
        assert found == question

    @pytest.mark.asyncio
    async def test_accepts_category_filter(self):
        session, result = _mock_session()
        question = _make_question()
        result.first.return_value = question

        found = await get_random_question(
            category=QuestionCategory.TECHNICAL,
            exclude_ids=None,
            session=session,
        )
        assert found == question


# ---------------------------------------------------------------------------
# get_question
# ---------------------------------------------------------------------------


class TestGetQuestion:
    @pytest.mark.asyncio
    async def test_returns_question_by_id(self):
        session, result = _mock_session()
        question = _make_question()
        result.first.return_value = question

        found = await get_question(question_id=question.id, session=session)
        assert found == question

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        session, result = _mock_session()
        result.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_question(question_id=uuid4(), session=session)
        assert exc_info.value.status_code == 404
        assert "Question not found" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# create_question
# ---------------------------------------------------------------------------


class TestCreateQuestion:
    @pytest.mark.asyncio
    async def test_creates_and_returns_question(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        payload = _make_question_create()
        user = _make_user()

        # After refresh, session.refresh should set the model's id
        async def _fake_refresh(obj):
            obj.id = uuid4()

        session.refresh.side_effect = _fake_refresh

        result = await create_question(payload=payload, session=session, _=user)

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()
        assert result.content == payload.content
        assert result.category == payload.category

    @pytest.mark.asyncio
    async def test_create_question_uses_payload_fields(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        payload = _make_question_create()
        user = _make_user()

        result = await create_question(payload=payload, session=session, _=user)

        # The returned Question object must have payload fields
        assert result.difficulty == Difficulty.HARD
        assert result.industry == Industry.SAAS
        assert result.role == Role.SOFTWARE_ENGINEER
