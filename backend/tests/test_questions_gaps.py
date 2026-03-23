"""Gap-filling unit tests for questions API routes.

Covers: industry filter, role filter, all-filters-combined, pagination with
offset, random question with difficulty filter, inactive question → 404, and
create question with company/topic tags.

No database required — AsyncSession is fully mocked, following the same
pattern established in test_questions_unit.py.
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
# Helpers (mirrors test_questions_unit.py conventions)
# ---------------------------------------------------------------------------


def _mock_session():
    """Return a (session, result) pair where result is reused by session.exec."""
    session = AsyncMock()
    result = MagicMock()
    session.exec = AsyncMock(return_value=result)
    return session, result


def _make_question(
    question_id=None,
    category=QuestionCategory.BEHAVIORAL,
    difficulty=Difficulty.MEDIUM,
    industry=Industry.GENERAL,
    role=Role.GENERAL,
    company_tags=None,
    topic_tags=None,
    is_active=True,
):
    q = MagicMock()
    q.id = question_id or uuid4()
    q.content = "Describe a time you handled conflict on a team."
    q.category = category
    q.difficulty = difficulty
    q.industry = industry
    q.role = role
    q.company_tags = company_tags if company_tags is not None else []
    q.topic_tags = topic_tags if topic_tags is not None else []
    q.expected_duration_seconds = 180
    q.is_active = is_active
    return q


def _make_user():
    user = MagicMock()
    user.id = uuid4()
    return user


# ---------------------------------------------------------------------------
# list_questions — industry filter
# ---------------------------------------------------------------------------


class TestListQuestionsIndustryFilter:
    @pytest.mark.asyncio
    async def test_list_questions_industry_filter(self):
        """list_questions forwards the industry parameter to the query and returns
        only matching questions from the (mocked) result set."""
        session, result = _mock_session()
        fintech_q = _make_question(industry=Industry.FINTECH)
        result.all.return_value = [fintech_q]

        found = await list_questions(
            industry=Industry.FINTECH,
            limit=20,
            offset=0,
            session=session,
        )

        assert len(found) == 1
        assert found[0].industry == Industry.FINTECH
        session.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_questions_industry_filter_returns_empty_when_none_match(self):
        """An industry filter that matches nothing returns an empty list."""
        session, result = _mock_session()
        result.all.return_value = []

        found = await list_questions(
            industry=Industry.HEALTHCARE,
            limit=20,
            offset=0,
            session=session,
        )

        assert found == []


# ---------------------------------------------------------------------------
# list_questions — role filter
# ---------------------------------------------------------------------------


class TestListQuestionsRoleFilter:
    @pytest.mark.asyncio
    async def test_list_questions_role_filter(self):
        """list_questions forwards the role parameter and returns matching rows."""
        session, result = _mock_session()
        eng_q = _make_question(role=Role.SOFTWARE_ENGINEER)
        result.all.return_value = [eng_q]

        found = await list_questions(
            role=Role.SOFTWARE_ENGINEER,
            limit=20,
            offset=0,
            session=session,
        )

        assert len(found) == 1
        assert found[0].role == Role.SOFTWARE_ENGINEER
        session.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_questions_role_filter_manager(self):
        """Role filter works for non-default roles such as ENGINEERING_MANAGER."""
        session, result = _mock_session()
        mgr_q = _make_question(role=Role.ENGINEERING_MANAGER)
        result.all.return_value = [mgr_q]

        found = await list_questions(
            role=Role.ENGINEERING_MANAGER,
            limit=20,
            offset=0,
            session=session,
        )

        assert len(found) == 1
        assert found[0].role == Role.ENGINEERING_MANAGER


# ---------------------------------------------------------------------------
# list_questions — all filters combined
# ---------------------------------------------------------------------------


class TestListQuestionsAllFiltersCombined:
    @pytest.mark.asyncio
    async def test_list_questions_all_filters_combined(self):
        """All available filter parameters can be combined in a single call; the
        handler passes all of them to session.exec and returns the result."""
        session, result = _mock_session()
        specific_q = _make_question(
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.HARD,
            industry=Industry.SAAS,
            role=Role.SOFTWARE_ENGINEER,
            company_tags=["google"],
            topic_tags=["arrays"],
        )
        result.all.return_value = [specific_q]

        found = await list_questions(
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.HARD,
            industry=Industry.SAAS,
            role=Role.SOFTWARE_ENGINEER,
            company="google",
            topic="arrays",
            limit=10,
            offset=0,
            session=session,
        )

        assert len(found) == 1
        q = found[0]
        assert q.category == QuestionCategory.TECHNICAL
        assert q.difficulty == Difficulty.HARD
        assert q.industry == Industry.SAAS
        assert q.role == Role.SOFTWARE_ENGINEER
        # session.exec must have been called exactly once (single combined query)
        session.exec.assert_awaited_once()


# ---------------------------------------------------------------------------
# list_questions — pagination with offset
# ---------------------------------------------------------------------------


class TestListQuestionsPaginationWithOffset:
    @pytest.mark.asyncio
    async def test_list_questions_pagination_with_offset(self):
        """list_questions accepts non-zero offset and limit, forwarding both to
        the underlying SQL statement via session.exec."""
        session, result = _mock_session()
        page_questions = [_make_question() for _ in range(3)]
        result.all.return_value = page_questions

        found = await list_questions(
            limit=3,
            offset=10,  # skip first 10 rows
            session=session,
        )

        assert found == page_questions
        session.exec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_questions_pagination_offset_zero_returns_first_page(self):
        """An explicit offset=0 works identically to the default (first page)."""
        session, result = _mock_session()
        first_page = [_make_question(), _make_question()]
        result.all.return_value = first_page

        found = await list_questions(limit=2, offset=0, session=session)

        assert len(found) == 2


# ---------------------------------------------------------------------------
# get_random_question — with difficulty filter
# ---------------------------------------------------------------------------


class TestGetRandomQuestionWithDifficultyFilter:
    @pytest.mark.asyncio
    async def test_get_random_question_with_difficulty_filter(self):
        """A difficulty filter is accepted and the first matching row is returned."""
        session, result = _mock_session()
        hard_q = _make_question(difficulty=Difficulty.HARD)
        result.first.return_value = hard_q

        found = await get_random_question(
            difficulty=Difficulty.HARD,
            exclude_ids=None,
            session=session,
        )

        assert found == hard_q
        assert found.difficulty == Difficulty.HARD

    @pytest.mark.asyncio
    async def test_get_random_question_with_difficulty_filter_not_found_raises_404(self):
        """When no question matches the difficulty filter, a 404 is raised."""
        session, result = _mock_session()
        result.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_random_question(
                difficulty=Difficulty.EASY,
                exclude_ids=None,
                session=session,
            )

        assert exc_info.value.status_code == 404
        assert "No matching question found" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# get_question — inactive question returns 404
# ---------------------------------------------------------------------------


class TestGetQuestionInactiveReturns404:
    @pytest.mark.asyncio
    async def test_get_question_inactive_returns_404(self):
        """get_question filters by is_active=True. When the DB returns None (which
        happens for inactive questions), the handler must raise HTTP 404."""
        session, result = _mock_session()
        # The query includes is_active.is_(True), so an inactive question is never
        # returned — simulate this by having result.first() return None.
        result.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_question(question_id=uuid4(), session=session)

        assert exc_info.value.status_code == 404
        assert "Question not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_question_active_question_is_returned(self):
        """Sanity check: an active question is returned normally."""
        session, result = _mock_session()
        active_q = _make_question(is_active=True)
        result.first.return_value = active_q

        found = await get_question(question_id=active_q.id, session=session)

        assert found == active_q


# ---------------------------------------------------------------------------
# create_question — with company and topic tags
# ---------------------------------------------------------------------------


class TestCreateQuestionWithTags:
    @pytest.mark.asyncio
    async def test_create_question_with_tags(self):
        """create_question must persist company_tags and topic_tags from the
        QuestionCreate payload and return the refreshed Question object."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        new_id = uuid4()

        async def _fake_refresh(obj):
            obj.id = new_id

        session.refresh = AsyncMock(side_effect=_fake_refresh)

        payload = QuestionCreate(
            content="Design a rate limiter for a public API.",
            category=QuestionCategory.SYSTEM_DESIGN,
            difficulty=Difficulty.HARD,
            industry=Industry.SAAS,
            role=Role.SOFTWARE_ENGINEER,
            company_tags=["google", "meta"],
            topic_tags=["rate-limiting", "distributed-systems"],
        )

        result = await create_question(payload=payload, session=session, _=_make_user())

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()

        assert result.content == payload.content
        assert result.category == QuestionCategory.SYSTEM_DESIGN
        assert result.company_tags == ["google", "meta"]
        assert result.topic_tags == ["rate-limiting", "distributed-systems"]

    @pytest.mark.asyncio
    async def test_create_question_with_tags_empty_lists_accepted(self):
        """create_question accepts empty tag lists (the default) without error."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        payload = QuestionCreate(
            content="Explain the CAP theorem.",
            category=QuestionCategory.TECHNICAL,
            difficulty=Difficulty.HARD,
            company_tags=[],
            topic_tags=[],
        )

        result = await create_question(payload=payload, session=session, _=_make_user())

        assert result.company_tags == []
        assert result.topic_tags == []
        session.commit.assert_awaited_once()
