"""Pure unit tests for interviews API route logic.

Tests all 12 endpoint groups plus the _get_interview_for_user helper.
No database required — all DB interactions mocked.

Coverage targets:
- POST /             create_interview (quota + analytics + remaining calc)
- GET /              list_interviews (filter, pagination)
- GET /{id}          get_interview
- POST /{id}/start   start_interview (question assignment, idempotency, error paths)
- GET /{id}/questions get_interview_questions (status gates, missing questions)
- POST /{id}/end     end_interview (duration calc, background task, analytics)
- DELETE /{id}       cancel_interview (status validation)
- POST /{id}/responses submit_response (question ownership, audio bg processing)
- GET /{id}/responses  get_responses (question embedding)
- GET /{id}/feedback   get_interview_feedback (placeholder)
- POST /quick-practice create_quick_practice (question lookup, type mapping)
- GET /{id}/export     export_interview_pdf (error routing)
- POST /{id}/share     create_share_link (error routing)
- GET /{id}/shares     list_share_links
- DELETE /shares/{id}  revoke_share_link (error routing)
- GET /shared/{token}  get_shared_interview (expired / not found)
- _get_interview_for_user helper (found / 404)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.interviews import (  # noqa: I001
    _get_interview_for_user,
    cancel_interview,
    create_interview,
    create_quick_practice,
    create_share_link,
    end_interview,
    export_interview_pdf,
    get_interview,
    get_interview_feedback,
    get_interview_questions,
    get_responses,
    get_shared_interview,
    list_interviews,
    list_share_links,
    revoke_share_link,
    start_interview,
    submit_response,
)
from app.models.interview import (
    InterviewResponseCreate,
    InterviewSessionCreate,
    InterviewStatus,
    InterviewType,
)
from app.models.user import SubscriptionTier

# ---------------------------------------------------------------------------
# Helpers
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


# ---------------------------------------------------------------------------
# _get_interview_for_user
# ---------------------------------------------------------------------------


class TestGetInterviewForUser:
    @pytest.mark.asyncio
    async def test_returns_interview_when_found(self):
        interview = _mock_interview()
        session = _exec_returning(interview)

        found = await _get_interview_for_user(session, uuid4(), uuid4())
        assert found is interview

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        session = _exec_returning(None)

        with pytest.raises(HTTPException) as exc_info:
            await _get_interview_for_user(session, uuid4(), uuid4())
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# POST / — create_interview
# ---------------------------------------------------------------------------


class TestCreateInterview:
    def _make_payload(self, interview_type=InterviewType.BEHAVIORAL, question_count=5):
        return InterviewSessionCreate(
            interview_type=interview_type,
            question_count=question_count,
        )

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    async def test_creates_interview_for_free_user(self, mock_get_analytics):
        analytics = MagicMock()
        mock_get_analytics.return_value = analytics

        user = _mock_user(interviews_this_month=1)
        session = _mock_session()

        async def fake_refresh(obj):
            # Copy attributes from our mock so the dict-building code works
            pass

        session.refresh = fake_refresh

        payload = self._make_payload()

        with patch("app.api.interviews.InterviewSession") as MockSession:
            instance = _mock_interview(user_id=user.id)
            MockSession.return_value = instance

            result = await create_interview(payload, user, session)

        assert result["status"] == InterviewStatus.SCHEDULED
        assert user.interviews_this_month == 2
        assert user.total_interviews == 1
        analytics.capture.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    async def test_free_user_gets_remaining_count(self, mock_get_analytics):
        mock_get_analytics.return_value = MagicMock()
        user = _mock_user(subscription_tier=SubscriptionTier.FREE, interviews_this_month=1)
        session = _mock_session()

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = _mock_interview(user_id=user.id)
            result = await create_interview(self._make_payload(), user, session)

        # After increment interviews_this_month == 2, remaining = max(0, 3-2) = 1
        assert result["remaining_interviews"] == 1

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    async def test_pro_user_gets_none_remaining(self, mock_get_analytics):
        mock_get_analytics.return_value = MagicMock()
        user = _mock_user(subscription_tier=SubscriptionTier.PRO, interviews_this_month=10)
        session = _mock_session()

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = _mock_interview(user_id=user.id)
            result = await create_interview(self._make_payload(), user, session)

        assert result["remaining_interviews"] is None

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    async def test_free_user_at_limit_gets_zero_remaining(self, mock_get_analytics):
        mock_get_analytics.return_value = MagicMock()
        # Already used 3 (limit), after increment = 4
        user = _mock_user(subscription_tier=SubscriptionTier.FREE, interviews_this_month=3)
        session = _mock_session()

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = _mock_interview(user_id=user.id)
            result = await create_interview(self._make_payload(), user, session)

        assert result["remaining_interviews"] == 0


# ---------------------------------------------------------------------------
# GET / — list_interviews
# ---------------------------------------------------------------------------


class TestListInterviews:
    @pytest.mark.asyncio
    async def test_returns_all_interviews_without_filter(self):
        user = _mock_user()
        session = _mock_session()
        interviews = [_mock_interview(), _mock_interview()]
        result_mock = MagicMock()
        result_mock.all.return_value = interviews
        session.exec.return_value = result_mock

        result = await list_interviews(
            status_filter=None,
            limit=20,
            offset=0,
            current_user=user,
            session=session,
        )
        assert result == interviews

    @pytest.mark.asyncio
    async def test_returns_filtered_interviews_by_status(self):
        user = _mock_user()
        session = _mock_session()
        completed = _mock_interview(status=InterviewStatus.COMPLETED)
        result_mock = MagicMock()
        result_mock.all.return_value = [completed]
        session.exec.return_value = result_mock

        result = await list_interviews(
            status_filter=InterviewStatus.COMPLETED,
            limit=20,
            offset=0,
            current_user=user,
            session=session,
        )
        assert len(result) == 1
        assert result[0].status == InterviewStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_interviews(self):
        user = _mock_user()
        session = _mock_session()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.exec.return_value = result_mock

        result = await list_interviews(
            status_filter=None,
            limit=20,
            offset=0,
            current_user=user,
            session=session,
        )
        assert result == []


# ---------------------------------------------------------------------------
# GET /{id} — get_interview
# ---------------------------------------------------------------------------


class TestGetInterview:
    @pytest.mark.asyncio
    async def test_returns_interview_for_user(self):
        user = _mock_user()
        interview = _mock_interview(user_id=user.id)
        session = _exec_returning(interview)

        result = await get_interview(interview.id, user, session)
        assert result is interview

    @pytest.mark.asyncio
    async def test_raises_404_for_other_users_interview(self):
        user = _mock_user()
        session = _exec_returning(None)  # not found for this user

        with pytest.raises(HTTPException) as exc_info:
            await get_interview(uuid4(), user, session)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /{id}/start — start_interview
# ---------------------------------------------------------------------------


class TestStartInterview:
    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_starts_scheduled_interview(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=5)
        session = _exec_returning(interview)

        # get_interview_questions returns correct count (no reassignment needed)
        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock() for _ in range(5)]
        )

        result = await start_interview(interview.id, user, session)

        assert result.status == InterviewStatus.IN_PROGRESS
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_starting_already_in_progress_is_idempotent(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS, question_count=3)
        session = _exec_returning(interview)

        # Questions already match — no reassignment
        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock() for _ in range(3)]
        )

        result = await start_interview(interview.id, user, session)
        assert result.status == InterviewStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_raises_400_for_completed_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.COMPLETED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await start_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400
        assert "Cannot start interview" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_400_for_cancelled_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.CANCELLED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await start_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_assigns_questions_when_count_mismatch(self, mock_svc):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=5)
        session = _exec_returning(interview)

        # No existing questions — triggers assignment
        mock_svc.get_interview_questions = AsyncMock(return_value=[])
        mock_svc.assign_questions = AsyncMock()

        with patch("app.api.interviews.get_analytics") as mock_analytics:
            mock_analytics.return_value = MagicMock()
            await start_interview(interview.id, user, session)

        mock_svc.assign_questions.assert_awaited_once_with(session, interview)

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_clears_partial_questions_before_reassignment(self, mock_svc):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=5)
        session = _exec_returning(interview)

        # 2 questions exist but 5 expected — partial assignment
        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock(), MagicMock()]
        )
        mock_svc.assign_questions = AsyncMock()

        with patch("app.api.interviews.get_analytics") as mock_analytics:
            mock_analytics.return_value = MagicMock()
            await start_interview(interview.id, user, session)

        # flush() is called after clearing partial questions
        session.flush.assert_awaited()
        mock_svc.assign_questions.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_raises_400_when_assign_questions_raises_value_error(self, mock_svc):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=5)
        session = _exec_returning(interview)

        mock_svc.get_interview_questions = AsyncMock(return_value=[])
        mock_svc.assign_questions = AsyncMock(side_effect=ValueError("Not enough questions"))

        with pytest.raises(HTTPException) as exc_info:
            await start_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400
        assert "Not enough questions" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_sets_started_at_on_first_start(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, started_at=None)
        interview.question_count = 3
        session = _exec_returning(interview)

        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock() for _ in range(3)]
        )

        await start_interview(interview.id, user, session)
        # started_at should have been set (truthy)
        assert interview.started_at is not None

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_does_not_overwrite_existing_started_at(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        user = _mock_user()
        original_start = datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC)
        interview = _mock_interview(
            status=InterviewStatus.IN_PROGRESS, started_at=original_start
        )
        interview.question_count = 2
        session = _exec_returning(interview)

        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock(), MagicMock()]
        )

        await start_interview(interview.id, user, session)
        # started_at should NOT have been overwritten
        assert interview.started_at == original_start

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_fires_analytics_interview_started(self, mock_svc, mock_get_analytics):
        analytics = MagicMock()
        mock_get_analytics.return_value = analytics
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=1)
        session = _exec_returning(interview)
        mock_svc.get_interview_questions = AsyncMock(return_value=[MagicMock()])

        await start_interview(interview.id, user, session)

        # Should have called capture twice: INTERVIEW_STARTED + ACTIVATION_STARTED
        assert analytics.capture.call_count == 2


# ---------------------------------------------------------------------------
# GET /{id}/questions — get_interview_questions
# ---------------------------------------------------------------------------


class TestGetInterviewQuestions:
    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_returns_questions_for_in_progress_interview(self, mock_svc):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        session = _exec_returning(interview)

        questions = [MagicMock(), MagicMock()]
        mock_svc.get_interview_questions = AsyncMock(return_value=questions)

        result = await get_interview_questions(interview.id, user, session)
        assert result == questions

    @pytest.mark.asyncio
    async def test_raises_400_for_scheduled_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await get_interview_questions(interview.id, user, session)
        assert exc_info.value.status_code == 400
        assert "not been started" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_raises_404_when_no_questions_assigned(self, mock_svc):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        session = _exec_returning(interview)

        mock_svc.get_interview_questions = AsyncMock(return_value=[])

        with pytest.raises(HTTPException) as exc_info:
            await get_interview_questions(interview.id, user, session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_if_interview_not_found(self):
        user = _mock_user()
        session = _exec_returning(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_interview_questions(uuid4(), user, session)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /{id}/end — end_interview
# ---------------------------------------------------------------------------


class TestEndInterview:
    @pytest.mark.asyncio
    @patch("app.api.interviews.background_tasks")
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.asyncio")
    async def test_ends_in_progress_interview(self, mock_asyncio, mock_analytics, mock_bg):
        mock_analytics.return_value = MagicMock()
        mock_asyncio.create_task = MagicMock()
        mock_bg.generate_session_feedback_async = AsyncMock()

        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        interview.started_at = datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC)
        session = _exec_returning(interview)

        result = await end_interview(interview.id, user, session)

        assert result.status == InterviewStatus.COMPLETED
        assert result.ended_at is not None
        assert result.duration_seconds >= 0
        session.commit.assert_awaited_once()
        mock_asyncio.create_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.background_tasks")
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.asyncio")
    async def test_ends_scheduled_interview_directly(self, mock_asyncio, mock_analytics, mock_bg):
        """Scheduled interview can also be ended (skipped interviews)."""
        mock_analytics.return_value = MagicMock()
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED)
        interview.started_at = None
        session = _exec_returning(interview)

        result = await end_interview(interview.id, user, session)

        assert result.status == InterviewStatus.COMPLETED
        # When started_at was None, both started_at and ended_at should be the same
        assert result.started_at == result.ended_at
        assert result.duration_seconds == 0

    @pytest.mark.asyncio
    async def test_raises_400_for_already_completed(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.COMPLETED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await end_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400
        assert "Cannot end interview" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_400_for_cancelled_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.CANCELLED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await end_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.interviews.background_tasks")
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.asyncio")
    async def test_fires_analytics_completed_and_activation(
        self, mock_asyncio, mock_get_analytics, mock_bg
    ):
        analytics = MagicMock()
        mock_get_analytics.return_value = analytics
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        interview.started_at = datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC)
        session = _exec_returning(interview)

        await end_interview(interview.id, user, session)

        assert analytics.capture.call_count == 2

    @pytest.mark.asyncio
    @patch("app.api.interviews.background_tasks")
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.asyncio")
    async def test_calculates_duration_from_started_at(
        self, mock_asyncio, mock_analytics, mock_bg
    ):
        mock_analytics.return_value = MagicMock()
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        # Fake a 120-second interview by patching _get_time
        started = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
        ended = datetime(2025, 6, 1, 10, 2, 0, tzinfo=UTC)
        interview.started_at = started
        session = _exec_returning(interview)

        with patch("app.api.interviews._get_time", return_value=ended):
            result = await end_interview(interview.id, user, session)

        assert result.duration_seconds == 120


# ---------------------------------------------------------------------------
# DELETE /{id} — cancel_interview
# ---------------------------------------------------------------------------


class TestCancelInterview:
    @pytest.mark.asyncio
    async def test_cancels_scheduled_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED)
        session = _exec_returning(interview)

        await cancel_interview(interview.id, user, session)

        assert interview.status == InterviewStatus.CANCELLED
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_400_for_in_progress_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400
        assert "scheduled" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raises_400_for_completed_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.COMPLETED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_for_cancelled_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.CANCELLED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_interview(interview.id, user, session)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_404_when_interview_not_found(self):
        user = _mock_user()
        session = _exec_returning(None)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_interview(uuid4(), user, session)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /{id}/responses — submit_response
# ---------------------------------------------------------------------------


class TestSubmitResponse:
    def _make_payload(self, question_id=None, transcript=None, audio_url=None):
        return InterviewResponseCreate(
            question_id=question_id or uuid4(),
            transcript=transcript,
            audio_url=audio_url,
            duration_seconds=90,
        )

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_submits_response_for_in_progress_interview(self, mock_asyncio):
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
        response_obj.word_count = None

        # session.exec is called twice:
        #  1) _get_interview_for_user -> returns interview
        #  2) question link check -> returns question_link
        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(first=question_link),
        ]

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, self._make_payload(question_id), user, session)

        session.add.assert_called_once_with(response_obj)
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_400_for_non_in_progress_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED)
        session = _exec_returning(interview)

        with pytest.raises(HTTPException) as exc_info:
            await submit_response(interview.id, self._make_payload(), user, session)
        assert exc_info.value.status_code == 400
        assert "in progress" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raises_400_when_question_not_in_interview(self):
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)

        session = _mock_session()
        results = [
            _make_exec_result(first=interview),
            _make_exec_result(first=None),  # question link not found
        ]
        session.exec.side_effect = results

        with pytest.raises(HTTPException) as exc_info:
            await submit_response(interview.id, self._make_payload(), user, session)
        assert exc_info.value.status_code == 400
        assert "does not belong" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_calculates_word_count_from_transcript(self, mock_asyncio):
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

        transcript = "Hello this is a test transcript with ten words total here"
        payload = self._make_payload(question_id=question_id, transcript=transcript)

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, payload, user, session)

        # word_count should be set to the number of words
        assert response_obj.word_count == len(transcript.split())

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_triggers_audio_processing_when_no_transcript(self, mock_asyncio):
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
        response_obj.word_count = None

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(first=question_link),
        ]

        payload = self._make_payload(question_id=question_id, audio_url="s3://audio.webm")

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, payload, user, session)

        # asyncio.create_task should have been called for background audio processing
        mock_asyncio.create_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.asyncio")
    async def test_no_audio_processing_when_transcript_provided(self, mock_asyncio):
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

        # Both audio_url AND transcript provided — no background task
        payload = self._make_payload(
            question_id=question_id, audio_url="s3://audio.webm", transcript="I said stuff"
        )

        with patch("app.api.interviews.InterviewResponse") as MockResponse:
            MockResponse.return_value = response_obj
            await submit_response(interview_id, payload, user, session)

        mock_asyncio.create_task.assert_not_called()


# ---------------------------------------------------------------------------
# GET /{id}/responses — get_responses
# ---------------------------------------------------------------------------


class TestGetResponses:
    @pytest.mark.asyncio
    async def test_returns_responses_with_embedded_questions(self):
        user = _mock_user()
        interview_id = uuid4()
        question_id = uuid4()

        interview = _mock_interview()
        interview.id = interview_id

        response = MagicMock()
        response.id = uuid4()
        response.session_id = interview_id
        response.question_id = question_id
        response.audio_url = None
        response.video_url = None
        response.transcript = "test"
        response.duration_seconds = 60
        response.word_count = 1
        response.filler_word_count = 0
        response.processing_status = "completed"
        response.processing_error = None
        response.created_at = datetime.now(UTC)

        question = MagicMock()
        question.id = question_id
        question.content = "Tell me about yourself"
        question.category = "behavioral"
        question.difficulty = "medium"

        session = _mock_session()
        # exec called 3 times:
        # 1) _get_interview_for_user
        # 2) fetch responses
        # 3) fetch questions
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(all=[response]),
            _make_exec_result(all=[question]),
        ]

        result = await get_responses(interview_id, user, session)

        assert len(result) == 1
        assert result[0]["question"] is not None
        assert result[0]["question"]["id"] == question_id

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_responses(self):
        user = _mock_user()
        interview = _mock_interview()

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(all=[]),
        ]

        result = await get_responses(interview.id, user, session)
        assert result == []

    @pytest.mark.asyncio
    async def test_embeds_none_for_missing_question(self):
        user = _mock_user()
        interview_id = uuid4()
        question_id = uuid4()

        interview = _mock_interview()
        interview.id = interview_id

        response = MagicMock()
        response.id = uuid4()
        response.session_id = interview_id
        response.question_id = question_id  # Question not in DB
        response.audio_url = None
        response.video_url = None
        response.transcript = None
        response.duration_seconds = 0
        response.word_count = None
        response.filler_word_count = None
        response.processing_status = "pending"
        response.processing_error = None
        response.created_at = datetime.now(UTC)

        session = _mock_session()
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(all=[response]),
            _make_exec_result(all=[]),  # no matching question
        ]

        result = await get_responses(interview_id, user, session)
        assert result[0]["question"] is None

    @pytest.mark.asyncio
    async def test_raises_404_when_interview_not_found(self):
        user = _mock_user()
        session = _exec_returning(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_responses(uuid4(), user, session)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# GET /{id}/feedback — get_interview_feedback (placeholder)
# ---------------------------------------------------------------------------


class TestGetInterviewFeedback:
    @pytest.mark.asyncio
    async def test_returns_placeholder_message(self):
        interview_id = uuid4()
        result = await get_interview_feedback(interview_id)
        assert "message" in result
        assert str(interview_id) in result["message"]


# ---------------------------------------------------------------------------
# POST /quick-practice — create_quick_practice
# ---------------------------------------------------------------------------


class TestCreateQuickPractice:
    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_creates_quick_practice_for_behavioral_question(
        self, mock_svc, mock_analytics
    ):
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user(subscription_tier=SubscriptionTier.FREE, interviews_this_month=0)
        question_id = uuid4()

        question = MagicMock()
        question.id = question_id
        question.category = "behavioral"
        question.company_tags = ["google"]
        question.is_active = True

        interview = _mock_interview(user_id=user.id, question_count=1)
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        assert result["question_count"] == 1
        assert user.interviews_this_month == 1
        mock_svc.assign_specific_question.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_404_when_question_not_found(self):
        user = _mock_user()
        session = _exec_returning(None)

        with pytest.raises(HTTPException) as exc_info:
            await create_quick_practice(uuid4(), user, session)
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.api.interviews.interview_service")
    async def test_raises_400_when_assign_specific_question_fails(self, mock_svc):
        mock_svc.assign_specific_question = AsyncMock(
            side_effect=ValueError("Cannot assign question")
        )

        user = _mock_user()
        question_id = uuid4()
        question = MagicMock()
        question.id = question_id
        question.category = "technical"
        question.company_tags = []
        question.is_active = True

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession"), pytest.raises(HTTPException) as exc_info:
            await create_quick_practice(question_id, user, session)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_maps_technical_category_to_technical_type(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user()
        question_id = uuid4()
        question = MagicMock()
        question.id = question_id
        question.category = "technical"
        question.company_tags = []
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.interview_type = InterviewType.TECHNICAL
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        assert result["interview_type"] == InterviewType.TECHNICAL

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_maps_system_design_category_correctly(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user()
        question_id = uuid4()
        question = MagicMock()
        question.id = question_id
        question.category = "system_design"
        question.company_tags = []
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.interview_type = InterviewType.SYSTEM_DESIGN
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        assert result["interview_type"] == InterviewType.SYSTEM_DESIGN

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_uses_company_tag_as_company_style(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user(subscription_tier=SubscriptionTier.PRO)
        question_id = uuid4()
        question = MagicMock()
        question.id = question_id
        question.category = "behavioral"
        question.company_tags = ["amazon"]
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.company_style = "amazon"
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        assert result["company_style"] == "amazon"

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_pro_user_gets_none_remaining(self, mock_svc, mock_analytics):
        mock_analytics.return_value = MagicMock()
        mock_svc.assign_specific_question = AsyncMock()

        user = _mock_user(subscription_tier=SubscriptionTier.PRO, interviews_this_month=50)
        question_id = uuid4()
        question = MagicMock()
        question.id = question_id
        question.category = "behavioral"
        question.company_tags = []
        question.is_active = True

        interview = _mock_interview(question_count=1)
        interview.target_company = None

        session = _mock_session()
        session.exec.return_value = _make_exec_result(first=question)

        with patch("app.api.interviews.InterviewSession") as MockSession:
            MockSession.return_value = interview
            result = await create_quick_practice(question_id, user, session)

        assert result["remaining_interviews"] is None


# ---------------------------------------------------------------------------
# GET /{id}/export — export_interview_pdf
# ---------------------------------------------------------------------------


class TestExportInterviewPdf:
    @pytest.mark.asyncio
    @patch("app.api.interviews.pdf_service")
    async def test_returns_pdf_response_on_success(self, mock_pdf_svc):
        pdf_bytes = b"%PDF-1.4 mock content"
        mock_pdf_svc.generate_interview_pdf = AsyncMock(return_value=pdf_bytes)

        user = _mock_user()
        session = _mock_session()
        interview_id = uuid4()

        from fastapi.responses import Response

        result = await export_interview_pdf(interview_id, session, user)

        assert isinstance(result, Response)
        assert result.media_type == "application/pdf"
        assert result.body == pdf_bytes

    @pytest.mark.asyncio
    @patch("app.api.interviews.pdf_service")
    async def test_raises_404_when_interview_not_found(self, mock_pdf_svc):
        mock_pdf_svc.generate_interview_pdf = AsyncMock(
            side_effect=ValueError("Interview not found")
        )

        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await export_interview_pdf(uuid4(), session, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.interviews.pdf_service")
    async def test_raises_403_when_access_denied(self, mock_pdf_svc):
        mock_pdf_svc.generate_interview_pdf = AsyncMock(
            side_effect=ValueError("Access denied to this resource")
        )

        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await export_interview_pdf(uuid4(), session, user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("app.api.interviews.pdf_service")
    async def test_raises_400_for_generic_value_error(self, mock_pdf_svc):
        mock_pdf_svc.generate_interview_pdf = AsyncMock(
            side_effect=ValueError("Some other validation error")
        )

        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await export_interview_pdf(uuid4(), session, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.interviews.pdf_service")
    async def test_includes_correct_filename_header(self, mock_pdf_svc):
        mock_pdf_svc.generate_interview_pdf = AsyncMock(return_value=b"pdf")
        user = _mock_user()
        session = _mock_session()
        interview_id = uuid4()

        result = await export_interview_pdf(interview_id, session, user)

        assert f"interview-{interview_id}.pdf" in result.headers["content-disposition"]


# ---------------------------------------------------------------------------
# POST /{id}/share — create_share_link
# ---------------------------------------------------------------------------


class TestCreateShareLink:
    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_creates_and_returns_share_link(self, mock_share_svc):
        share = MagicMock()
        share.id = uuid4()
        share.interview_id = uuid4()
        share.token = "abc123token"
        share.expires_at = datetime.now(UTC)
        share.view_count = 0
        share.created_at = datetime.now(UTC)

        mock_share_svc.create_share_link = AsyncMock(return_value=share)
        user = _mock_user()
        session = _mock_session()

        from app.models.interview_share import InterviewShareRead

        result = await create_share_link(uuid4(), session, user)

        assert isinstance(result, InterviewShareRead)
        assert result.token == "abc123token"
        assert result.share_url == f"/shared/{share.token}"

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_raises_404_when_interview_not_found(self, mock_share_svc):
        mock_share_svc.create_share_link = AsyncMock(
            side_effect=ValueError("Interview not found")
        )
        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await create_share_link(uuid4(), session, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_raises_403_for_other_value_errors(self, mock_share_svc):
        mock_share_svc.create_share_link = AsyncMock(
            side_effect=ValueError("You don't have permission")
        )
        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await create_share_link(uuid4(), session, user)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# GET /{id}/shares — list_share_links
# ---------------------------------------------------------------------------


class TestListShareLinks:
    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_returns_list_of_shares(self, mock_share_svc):
        share1 = MagicMock()
        share1.id = uuid4()
        share1.interview_id = uuid4()
        share1.token = "token1"
        share1.expires_at = datetime.now(UTC)
        share1.view_count = 3
        share1.created_at = datetime.now(UTC)

        share2 = MagicMock()
        share2.id = uuid4()
        share2.interview_id = uuid4()
        share2.token = "token2"
        share2.expires_at = datetime.now(UTC)
        share2.view_count = 0
        share2.created_at = datetime.now(UTC)

        mock_share_svc.get_shares_for_interview = AsyncMock(return_value=[share1, share2])
        user = _mock_user()
        session = _mock_session()

        result = await list_share_links(uuid4(), session, user)

        assert len(result) == 2
        assert result[0].token == "token1"
        assert result[1].share_url == "/shared/token2"

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_returns_empty_list_when_no_shares(self, mock_share_svc):
        mock_share_svc.get_shares_for_interview = AsyncMock(return_value=[])
        user = _mock_user()
        session = _mock_session()

        result = await list_share_links(uuid4(), session, user)
        assert result == []


# ---------------------------------------------------------------------------
# DELETE /shares/{id} — revoke_share_link
# ---------------------------------------------------------------------------


class TestRevokeShareLink:
    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_revokes_share_link_successfully(self, mock_share_svc):
        mock_share_svc.revoke_share_link = AsyncMock()
        user = _mock_user()
        session = _mock_session()

        # Should not raise
        await revoke_share_link(uuid4(), session, user)
        mock_share_svc.revoke_share_link.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_raises_404_when_share_not_found(self, mock_share_svc):
        mock_share_svc.revoke_share_link = AsyncMock(
            side_effect=ValueError("Share link not found")
        )
        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await revoke_share_link(uuid4(), session, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_raises_403_for_permission_errors(self, mock_share_svc):
        mock_share_svc.revoke_share_link = AsyncMock(
            side_effect=ValueError("Permission denied")
        )
        user = _mock_user()
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await revoke_share_link(uuid4(), session, user)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# GET /shared/{token} — get_shared_interview
# ---------------------------------------------------------------------------


class TestGetSharedInterview:
    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_returns_shared_interview_data(self, mock_share_svc):
        from app.models.interview_share import SharedInterviewRead

        shared_data = SharedInterviewRead(
            interview_type="behavioral",
            overall_score=8.5,
            audio_score=7.0,
            content_score=9.0,
            question_count=5,
            created_at=datetime.now(UTC),
            shared_by="John",
            responses=[],
        )
        mock_share_svc.get_shared_interview = AsyncMock(return_value=shared_data)
        session = _mock_session()

        result = await get_shared_interview("valid-token-abc", session)

        assert result.interview_type == "behavioral"
        assert result.overall_score == 8.5
        assert result.shared_by == "John"

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_raises_410_when_link_expired(self, mock_share_svc):
        mock_share_svc.get_shared_interview = AsyncMock(
            side_effect=ValueError("Share link has expired")
        )
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await get_shared_interview("expired-token", session)
        assert exc_info.value.status_code == 410
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.api.interviews.share_service")
    async def test_raises_404_when_token_not_found(self, mock_share_svc):
        mock_share_svc.get_shared_interview = AsyncMock(
            side_effect=ValueError("Token does not exist")
        )
        session = _mock_session()

        with pytest.raises(HTTPException) as exc_info:
            await get_shared_interview("unknown-token", session)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Additional edge-case / integration-style unit tests
# ---------------------------------------------------------------------------


class TestStartInterviewAnalyticsProperties:
    """Verify analytics capture calls include required keys."""

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.interview_service")
    async def test_analytics_payload_contains_interview_id(self, mock_svc, mock_get_analytics):
        analytics = MagicMock()
        mock_get_analytics.return_value = analytics
        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.SCHEDULED, question_count=2)
        session = _exec_returning(interview)
        mock_svc.get_interview_questions = AsyncMock(
            return_value=[MagicMock(), MagicMock()]
        )

        await start_interview(interview.id, user, session)

        call_kwargs = analytics.capture.call_args_list[0][1]
        assert "interview_id" in call_kwargs["properties"]
        assert call_kwargs["properties"]["interview_id"] == str(interview.id)


class TestCreateInterviewAnalyticsProperties:
    """Verify create_interview analytics call properties."""

    @pytest.mark.asyncio
    @patch("app.api.interviews.get_analytics")
    async def test_analytics_capture_on_create(self, mock_get_analytics):
        analytics = MagicMock()
        mock_get_analytics.return_value = analytics
        user = _mock_user()
        session = _mock_session()

        with patch("app.api.interviews.InterviewSession") as MockSession:
            instance = _mock_interview(user_id=user.id)
            MockSession.return_value = instance
            await create_interview(
                InterviewSessionCreate(interview_type=InterviewType.TECHNICAL),
                user,
                session,
            )

        analytics.capture.assert_called_once()
        props = analytics.capture.call_args[1]["properties"]
        assert "interview_type" in props
        assert "question_count" in props


class TestEndInterviewDurationWithNoStartedAt:
    """When started_at is None, ended_at = started_at so duration = 0."""

    @pytest.mark.asyncio
    @patch("app.api.interviews.background_tasks")
    @patch("app.api.interviews.get_analytics")
    @patch("app.api.interviews.asyncio")
    async def test_zero_duration_when_no_started_at(self, mock_asyncio, mock_analytics, mock_bg):
        mock_analytics.return_value = MagicMock()
        mock_asyncio.create_task = MagicMock()

        user = _mock_user()
        interview = _mock_interview(status=InterviewStatus.IN_PROGRESS)
        interview.started_at = None
        session = _exec_returning(interview)

        result = await end_interview(interview.id, user, session)

        assert result.duration_seconds == 0


class TestResponsesNoQuestionsSkipsExec:
    """If responses list is empty, no second exec for questions."""

    @pytest.mark.asyncio
    async def test_empty_responses_skips_question_lookup(self):
        user = _mock_user()
        interview = _mock_interview()

        session = _mock_session()
        # exec called only twice: _get_interview_for_user + fetch responses
        session.exec.side_effect = [
            _make_exec_result(first=interview),
            _make_exec_result(all=[]),
        ]

        result = await get_responses(interview.id, user, session)

        assert result == []
        # Only two exec calls, no third call for questions
        assert session.exec.call_count == 2


# ---------------------------------------------------------------------------
# Internal helper to create side-effect-friendly exec results
# ---------------------------------------------------------------------------


def _make_exec_result(first=None, all=None):
    """Create a MagicMock exec result with configurable .first() and .all()."""
    mock = MagicMock()
    mock.first.return_value = first
    mock.all.return_value = all if all is not None else ([] if first is None else [first])
    return mock
