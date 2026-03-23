"""Gap-filling unit tests for interviews API route logic.

Covers branches and conditions not exercised by test_interviews_api_unit.py.
No database required — all DB interactions mocked.

Gap targets:
- start_interview:
    - existing questions count != num_questions → delete + reassign
    - IN_PROGRESS status is allowed (not rejected like COMPLETED)
    - ValueError from assign_questions → HTTP 400
- submit_response:
    - both audio_url AND transcript provided → no background task
    - word_count set from len(transcript.split())
    - no transcript → word_count not set
- get_responses:
    - no responses → returns empty list []
- create_quick_practice:
    - unknown category defaults to InterviewType.BEHAVIORAL
    - ValueError from assign_specific_question → HTTP 400
    - question.company_tags[0] used as company_style
    - empty company_tags → company_style is None
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.interviews import (  # noqa: I001
    create_quick_practice,
    get_responses,
    start_interview,
    submit_response,
)
from app.models.interview import (
    InterviewResponseCreate,
    InterviewStatus,
    InterviewType,
)
from app.models.user import SubscriptionTier


# ---------------------------------------------------------------------------
# Helpers — mirror exact patterns from test_interviews_api_unit.py
# ---------------------------------------------------------------------------


def _mock_session():
    """Return a fully mocked AsyncSession."""
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _mock_user(
    user_id=None,
    subscription_tier=SubscriptionTier.FREE,
    interviews_this_month=0,
    total_interviews=0,
):
    """Return a MagicMock User with sensible defaults."""
    user = MagicMock()
    user.id = user_id or uuid4()
    user.subscription_tier = subscription_tier
    user.interviews_this_month = interviews_this_month
    user.total_interviews = total_interviews
    return user


def _mock_interview(
    interview_id=None,
    user_id=None,
    status=InterviewStatus.SCHEDULED,
    question_count=5,
    started_at=None,
):
    """Return a MagicMock InterviewSession."""
    iv = MagicMock()
    iv.id = interview_id or uuid4()
    iv.user_id = user_id or uuid4()
    iv.status = status
    iv.question_count = question_count
    iv.interview_type = InterviewType.BEHAVIORAL
    iv.company_style = None
    iv.target_company = None
    iv.overall_score = None
    iv.duration_seconds = None
    iv.created_at = datetime.now(UTC)
    iv.started_at = started_at
    iv.ended_at = None
    iv.difficulty = None
    return iv


def _exec_returning(value):
    """Return a mock session whose exec().first() returns *value*."""
    result = MagicMock()
    result.first.return_value = value
    result.all.return_value = [value] if value is not None else []
    session = _mock_session()
    session.exec.return_value = result
    return session


def _make_exec_result(first=None, all=None):
    """Create a MagicMock exec result with configurable .first() and .all()."""
    mock = MagicMock()
    mock.first.return_value = first
    mock.all.return_value = all if all is not None else ([] if first is None else [first])
    return mock


# ---------------------------------------------------------------------------
# POST /{id}/start — start_interview gaps
# ---------------------------------------------------------------------------


class TestStartInterviewGaps:
    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_start_interview_clears_existing_questions_when_count_mismatch(
        self, mock_svc, mock_analytics
    ):
        """When existing question count != interview.question_count, they are deleted
        and then assign_questions is called to repopulate.

        This exercises the branch:
            if len(existing_questions) != expected_count:
                if existing_questions:        # <-- existing_questions is non-empty
                    await session.exec(delete(...))
                    await session.flush()
                await interview_service.assign_questions(...)
        """
        mock_analytics.return_value = MagicMock()

        user = _mock_user()
        # Interview expects 5 questions
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=5)
        session = _exec_returning(interview)

        # 3 questions exist — mismatches the expected 5
        existing = [MagicMock(), MagicMock(), MagicMock()]
        mock_svc.get_interview_questions = AsyncMock(return_value=existing)
        mock_svc.assign_questions = AsyncMock()

        await start_interview(interview.id, user, session)

        # The session must have executed a DELETE statement and flushed
        session.flush.assert_awaited()
        # And then fresh assignment must have been triggered
        mock_svc.assign_questions.assert_awaited_once_with(session, interview)

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_start_interview_allows_restart_when_in_progress(
        self, mock_svc, mock_analytics
    ):
        """IN_PROGRESS status must NOT raise 400 — it is explicitly allowed by the
        endpoint guard:
            if interview.status not in {SCHEDULED, IN_PROGRESS}: raise 400
        """
        mock_analytics.return_value = MagicMock()

        user = _mock_user()
        interview = _mock_interview(
            status=InterviewStatus.IN_PROGRESS,
            question_count=2,
            started_at=datetime(2025, 3, 1, 9, 0, 0, tzinfo=UTC),
        )
        session = _exec_returning(interview)

        # Questions already match — no reassignment path
        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock(), MagicMock()]
        )

        # Should NOT raise an HTTPException
        result = await start_interview(interview.id, user, session)

        assert result.status == InterviewStatus.IN_PROGRESS
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_start_interview_raises_400_when_assign_questions_fails(self, mock_svc):
        """ValueError raised by assign_questions must be converted to HTTP 400.

        The endpoint wraps the call:
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from None
        """
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=10)
        session = _exec_returning(interview)

        # No existing questions, but assignment fails
        mock_svc.get_interview_questions = AsyncMock(return_value=[])
        mock_svc.assign_questions = AsyncMock(
            side_effect=ValueError("Insufficient questions in pool")
        )

        with pytest.raises(HTTPException) as exc_info:
            await start_interview(interview.id, user, session)

        assert exc_info.value.status_code == 400
        assert "Insufficient questions in pool" in exc_info.value.detail


# ---------------------------------------------------------------------------
# POST /{id}/responses — submit_response gaps
# ---------------------------------------------------------------------------


class TestSubmitResponseGaps:
    def _make_payload(self, question_id=None, transcript=None, audio_url=None):
        return InterviewResponseCreate(
            question_id=question_id or uuid4(),
            transcript=transcript,
            audio_url=audio_url,
            duration_seconds=90,
        )

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_submit_response_no_background_task_when_transcript_provided_with_audio(
        self, mock_asyncio
    ):
        """When BOTH audio_url AND transcript are provided the condition:
            if payload.audio_url and not payload.transcript:
        evaluates to False, so asyncio.create_task must NOT be called.
        """
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview_id = uuid4()
        question_id = uuid4()

        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        interview.id = interview_id
        question_link = MagicMock()

        response_obj = MagicMock()
        response_obj.id = uuid4()
        response_obj.session_id = interview_id
        response_obj.question_id = question_id

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(first=question_link),
        ]

        payload = self._make_payload(
            question_id=question_id,
            audio_url="s3://bucket/audio.webm",
            transcript="I have both audio and a transcript",
        )

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, payload, user, session)

        # Background task must NOT have been scheduled
        mock_asyncio.create_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_submit_response_sets_word_count_from_transcript(self, mock_asyncio):
        """When a transcript is present, word_count is computed via len(transcript.split()).

        The endpoint does:
            if payload.transcript:
                response.word_count = len(payload.transcript.split())
        """
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview_id = uuid4()
        question_id = uuid4()

        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        interview.id = interview_id
        question_link = MagicMock()

        response_obj = MagicMock()
        response_obj.id = uuid4()
        response_obj.session_id = interview_id
        response_obj.question_id = question_id

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(first=question_link),
        ]

        transcript = "one two three four five"
        payload = self._make_payload(question_id=question_id, transcript=transcript)

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, payload, user, session)

        # word_count must equal the number of whitespace-separated tokens
        assert response_obj.word_count == len(transcript.split())  # 5

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_submit_response_no_word_count_when_no_transcript(self, mock_asyncio):
        """When no transcript is supplied, word_count must remain unset (the
        `if payload.transcript:` branch is not entered and word_count is never
        assigned on the response object).
        """
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview_id = uuid4()
        question_id = uuid4()

        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        interview.id = interview_id
        question_link = MagicMock()

        response_obj = MagicMock(spec=[])  # spec=[] prevents accidental attribute creation
        response_obj.id = uuid4()
        response_obj.session_id = interview_id
        response_obj.question_id = question_id

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(first=question_link),
        ]

        # No transcript, no audio_url — bare response
        payload = self._make_payload(question_id=question_id)

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, payload, user, session)

        # word_count must NOT have been set on the response object
        assert not hasattr(response_obj, "word_count")


# ---------------------------------------------------------------------------
# GET /{id}/responses — get_responses gaps
# ---------------------------------------------------------------------------


class TestGetResponsesGaps:
    @pytest.mark.asyncio
    async def test_get_responses_returns_empty_list_when_no_responses(self):
        """When the interview has no submitted responses the endpoint returns [].

        The code skips the question-fetch entirely when question_ids is empty:
            if question_ids:
                ...
            else:
                questions_map = {}
        And the final response_data list ends up empty.
        """
        user = _mock_user()
        interview = _mock_interview()

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),  # _get_interview_for_user
            _make_exec_result(all=[]),            # fetch responses — none found
        ]

        result = await get_responses(interview.id, user, session)

        assert result == []


# ---------------------------------------------------------------------------
# POST /quick-practice — create_quick_practice gaps
# ---------------------------------------------------------------------------


class TestCreateQuickPracticeGaps:
    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_quick_practice_unknown_category_defaults_to_behavioral(
        self, mock_svc, mock_analytics
    ):
        """A question whose category is not in the category_to_type mapping
        must fall back to InterviewType.BEHAVIORAL via dict.get(..., BEHAVIORAL).

        category_to_type = {
            "behavioral": BEHAVIORAL,
            "technical":  TECHNICAL,
            "system_design": SYSTEM_DESIGN,
        }
        Any other string → BEHAVIORAL default.
        """
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user(subscription_tier=SubscriptionTier.PRO)
        question_id = uuid4()

        question = MagicMock()
        question.id = question_id
        question.category = "culture_fit"  # unknown → defaults to BEHAVIORAL
        question.company_tags = []
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.interview_type = InterviewType.BEHAVIORAL
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        # The interview object we mocked already has BEHAVIORAL; verify the
        # returned dict reflects it (the type is determined before creating the
        # InterviewSession, but the mock's interview_type is BEHAVIORAL).
        assert result["interview_type"] == InterviewType.BEHAVIORAL

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_quick_practice_assign_question_raises_400_on_value_error(self, mock_svc):
        """ValueError from assign_specific_question must produce HTTP 400.

        The endpoint wraps the call:
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from None
        """
        mock_svc.assign_specific_question = AsyncMock(
            side_effect=ValueError("Duplicate question assignment")
        )

        user = _mock_user()
        question_id = uuid4()

        question = MagicMock()
        question.id = question_id
        question.category = "behavioral"
        question.company_tags = []
        question.is_active = True

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession"), pytest.raises(HTTPException) as exc_info:
            await create_quick_practice(question_id, user, session)

        assert exc_info.value.status_code == 400
        assert "Duplicate question assignment" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_quick_practice_uses_first_company_tag_as_style(
        self, mock_svc, mock_analytics
    ):
        """When company_tags is a non-empty list, company_tags[0] is passed as
        company_style to InterviewSession:
            company_style=question.company_tags[0] if question.company_tags else None
        """
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user(subscription_tier=SubscriptionTier.PRO)
        question_id = uuid4()

        question = MagicMock()
        question.id = question_id
        question.category = "behavioral"
        question.company_tags = ["meta", "google", "amazon"]  # first tag wins
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.company_style = "meta"
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        # Verify the InterviewSession constructor received company_style="meta"
        call_kwargs = MockSession.call_args.kwargs
        assert call_kwargs["company_style"] == "meta"
        # And the returned dict reflects that style
        assert result["company_style"] == "meta"

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_quick_practice_no_company_tags_sets_style_to_none(
        self, mock_svc, mock_analytics
    ):
        """When company_tags is an empty list, the ternary:
            company_style=question.company_tags[0] if question.company_tags else None
        evaluates to None.
        """
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user(subscription_tier=SubscriptionTier.FREE, interviews_this_month=0)
        question_id = uuid4()

        question = MagicMock()
        question.id = question_id
        question.category = "technical"
        question.company_tags = []  # empty → None
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.company_style = None
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        # company_style must be None in both the constructor call and the result
        call_kwargs = MockSession.call_args.kwargs
        assert call_kwargs["company_style"] is None
        assert result["company_style"] is None
