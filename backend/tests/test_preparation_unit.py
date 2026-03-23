"""Pure unit tests for preparation API routes.

Tests tier checks, start preparation, get state, draft CRUD,
practice start/submit, rate delivery, get comparison, and
list preparations — all with mocked DB sessions and services.
No database required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.preparation import (
    check_preparation_tier,
    get_draft,
    get_preparation_state,
    get_stage_value,
    list_preparations,
    rate_delivery,
    start_practice,
    start_preparation,
    update_draft,
)
from app.models.preparation import AnswerPreparation, DeliveryAttempt, PreparationStage
from app.models.user import SubscriptionTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_session():
    session = AsyncMock()
    result = MagicMock()
    session.exec = AsyncMock(return_value=result)
    return session, result


def _make_user(tier=SubscriptionTier.PRO):
    user = MagicMock()
    user.id = uuid4()
    user.subscription_tier = tier
    user.experience_level = "mid"
    return user


def _make_preparation(
    prep_id=None,
    user_id=None,
    stage=PreparationStage.DETECTIVE,
    draft=None,
):
    prep = MagicMock(spec=AnswerPreparation)
    prep.id = prep_id or uuid4()
    prep.user_id = user_id or uuid4()
    prep.question_id = uuid4()
    prep.stage = stage
    prep.draft_answer = draft
    prep.created_at = datetime.now(UTC)
    prep.updated_at = datetime.now(UTC)
    return prep


def _make_question():
    q = MagicMock()
    q.id = uuid4()
    q.content = "Tell me about a challenging project."
    q.category = "behavioral"
    q.difficulty = "medium"
    q.company_tags = []
    return q


def _make_attempt(prep_id=None, transcript="I did X then Y.", score=85.0):
    attempt = MagicMock(spec=DeliveryAttempt)
    attempt.id = uuid4()
    attempt.preparation_id = prep_id or uuid4()
    attempt.audio_url = "/uploads/audio/test.webm"
    attempt.transcript = transcript
    attempt.delivery_score = score
    attempt.comparison_feedback = "Good coverage."
    attempt.comparison_details = {"strengths": ["clarity"], "improvements": ["pacing"]}
    attempt.created_at = datetime.now(UTC)
    return attempt


# ---------------------------------------------------------------------------
# get_stage_value
# ---------------------------------------------------------------------------


class TestGetStageValue:
    def test_returns_value_for_enum(self):
        assert get_stage_value(PreparationStage.DETECTIVE) == "detective"
        assert get_stage_value(PreparationStage.DRAFT) == "draft"
        assert get_stage_value(PreparationStage.PRACTICE) == "practice"
        assert get_stage_value(PreparationStage.COMPLETE) == "complete"

    def test_returns_string_as_is(self):
        assert get_stage_value("detective") == "detective"

    def test_returns_detective_for_none(self):
        assert get_stage_value(None) == "detective"


# ---------------------------------------------------------------------------
# check_preparation_tier
# ---------------------------------------------------------------------------


class TestCheckPreparationTier:
    def test_allows_pro_user(self):
        user = _make_user(SubscriptionTier.PRO)
        check_preparation_tier(user)  # should not raise

    def test_allows_team_user(self):
        user = _make_user(SubscriptionTier.TEAM)
        check_preparation_tier(user)  # should not raise

    def test_raises_402_for_free_user(self):
        user = _make_user(SubscriptionTier.FREE)
        with pytest.raises(HTTPException) as exc_info:
            check_preparation_tier(user)
        assert exc_info.value.status_code == 402
        assert "Pro and Premium" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# list_preparations
# ---------------------------------------------------------------------------


class TestListPreparations:
    @pytest.mark.asyncio
    async def test_raises_402_for_free_user(self):
        session, _ = _mock_session()
        user = _make_user(SubscriptionTier.FREE)

        with pytest.raises(HTTPException) as exc_info:
            await list_preparations(current_user=user, session=session)
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_preparations(self):
        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.all.return_value = []
        session.exec = AsyncMock(return_value=prep_result)

        user = _make_user(SubscriptionTier.PRO)
        response = await list_preparations(current_user=user, session=session)
        assert response.preparations == []

    @pytest.mark.asyncio
    async def test_returns_preparations_with_question_content(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(user_id=user.id)
        question = _make_question()

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.all.return_value = [prep]
        q_result = MagicMock()
        q_result.first.return_value = question

        # First exec returns preparations, second returns question
        session.exec = AsyncMock(side_effect=[prep_result, q_result])

        response = await list_preparations(current_user=user, session=session)
        assert len(response.preparations) == 1
        assert response.preparations[0].question_content == question.content


# ---------------------------------------------------------------------------
# start_preparation
# ---------------------------------------------------------------------------


class TestStartPreparation:
    @pytest.mark.asyncio
    async def test_raises_402_for_free_user(self):
        session, _ = _mock_session()
        user = _make_user(SubscriptionTier.FREE)
        from app.api.preparation import PreparationStartRequest

        req = PreparationStartRequest(question_id=uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await start_preparation(request=req, current_user=user, session=session)
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_raises_404_when_question_not_found(self):
        user = _make_user(SubscriptionTier.PRO)
        session = AsyncMock()
        q_result = MagicMock()
        q_result.first.return_value = None
        session.exec = AsyncMock(return_value=q_result)

        from app.api.preparation import PreparationStartRequest

        req = PreparationStartRequest(question_id=uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await start_preparation(request=req, current_user=user, session=session)
        assert exc_info.value.status_code == 404
        assert "Question not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_resumes_existing_preparation(self):
        user = _make_user(SubscriptionTier.PRO)
        existing_prep = _make_preparation(user_id=user.id, stage=PreparationStage.DRAFT)
        question = _make_question()

        session = AsyncMock()
        q_result = MagicMock()
        q_result.first.return_value = question
        existing_result = MagicMock()
        existing_result.first.return_value = existing_prep
        session.exec = AsyncMock(side_effect=[q_result, existing_result])

        from app.api.preparation import PreparationStartRequest

        req = PreparationStartRequest(question_id=question.id)
        response = await start_preparation(request=req, current_user=user, session=session)
        assert response.preparation_id == existing_prep.id
        assert "Resuming" in response.message

    @pytest.mark.asyncio
    async def test_creates_new_preparation(self):
        user = _make_user(SubscriptionTier.PRO)
        question = _make_question()

        session = AsyncMock()
        q_result = MagicMock()
        q_result.first.return_value = question
        existing_result = MagicMock()
        existing_result.first.return_value = None  # no existing prep
        session.exec = AsyncMock(side_effect=[q_result, existing_result])
        session.add = MagicMock()
        session.commit = AsyncMock()

        async def _fake_refresh(obj):
            obj.id = uuid4()
            obj.stage = PreparationStage.DETECTIVE

        session.refresh = AsyncMock(side_effect=_fake_refresh)

        from app.api.preparation import PreparationStartRequest

        req = PreparationStartRequest(question_id=question.id)
        response = await start_preparation(request=req, current_user=user, session=session)
        assert response.stage == "detective"
        session.add.assert_called_once()


# ---------------------------------------------------------------------------
# get_preparation_state
# ---------------------------------------------------------------------------


class TestGetPreparationState:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_preparation_state(preparation_id=uuid4(), current_user=user, session=session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_state_with_all_fields(self):
        user = _make_user()
        prep = _make_preparation(user_id=user.id, stage=PreparationStage.PRACTICE)
        question = _make_question()

        from app.models.preparation import PreparationQnA

        qna = MagicMock(spec=PreparationQnA)
        qna.question = "Tell me more?"
        qna.answer = "I worked on X."
        qna.order = 1

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [qna]
        attempts_result = MagicMock()
        attempts_result.all.return_value = []
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result, attempts_result])

        state = await get_preparation_state(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert state.preparation_id == prep.id
        assert state.stage == "practice"
        assert state.question.content == question.content


# ---------------------------------------------------------------------------
# get_draft
# ---------------------------------------------------------------------------


class TestGetDraft:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_draft(preparation_id=uuid4(), current_user=user, session=session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_when_draft_not_generated(self):
        user = _make_user()
        prep = _make_preparation(draft=None)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_draft(preparation_id=prep.id, current_user=user, session=session)
        assert exc_info.value.status_code == 404
        assert "Draft not yet generated" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_returns_draft_when_available(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="My STAR draft.")
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        response = await get_draft(preparation_id=prep.id, current_user=user, session=session)
        assert response.draft_answer == "My STAR draft."


# ---------------------------------------------------------------------------
# update_draft
# ---------------------------------------------------------------------------


class TestUpdateDraft:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user(SubscriptionTier.PRO)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import DraftUpdateRequest

        req = DraftUpdateRequest(draft_answer="Updated draft.")
        with pytest.raises(HTTPException) as exc_info:
            await update_draft(
                preparation_id=uuid4(), request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_400_when_no_draft_to_update(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(draft=None, stage=PreparationStage.DETECTIVE)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import DraftUpdateRequest

        req = DraftUpdateRequest(draft_answer="Updated draft.")
        with pytest.raises(HTTPException) as exc_info:
            await update_draft(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_updates_draft_successfully(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="Old draft.")
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        from app.api.preparation import DraftUpdateRequest

        req = DraftUpdateRequest(draft_answer="New improved draft.")
        await update_draft(preparation_id=prep.id, request=req, current_user=user, session=session)
        assert prep.draft_answer == "New improved draft."
        session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# start_practice
# ---------------------------------------------------------------------------


class TestStartPractice:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user(SubscriptionTier.PRO)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await start_practice(preparation_id=uuid4(), current_user=user, session=session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_400_when_no_draft(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(stage=PreparationStage.DETECTIVE, draft=None)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await start_practice(preparation_id=prep.id, current_user=user, session=session)
        assert exc_info.value.status_code == 400
        assert "Draft not yet generated" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_creates_delivery_attempt(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="STAR answer here.")
        attempt = _make_attempt(prep_id=prep.id)

        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)
        session.add = MagicMock()
        session.commit = AsyncMock()

        async def _fake_refresh(obj):
            obj.id = attempt.id

        session.refresh = AsyncMock(side_effect=_fake_refresh)

        response = await start_practice(preparation_id=prep.id, current_user=user, session=session)
        assert response.stage == "practice"
        session.add.assert_called_once()


# ---------------------------------------------------------------------------
# rate_delivery
# ---------------------------------------------------------------------------


class TestRateDelivery:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user(SubscriptionTier.PRO)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await rate_delivery(
                preparation_id=uuid4(), request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_400_when_no_draft(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(draft=None, stage=PreparationStage.PRACTICE)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await rate_delivery(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 400
        assert "Draft not yet generated" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_raises_404_when_attempt_not_found(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="Draft content.")
        attempt_id = uuid4()

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = None
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=attempt_id)
        with pytest.raises(HTTPException) as exc_info:
            await rate_delivery(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 404
        assert "Delivery attempt not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_raises_400_when_attempt_has_no_transcript(self):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="Draft content.")
        attempt = _make_attempt(prep_id=prep.id, transcript=None)
        attempt.transcript = None

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=attempt.id)
        with pytest.raises(HTTPException) as exc_info:
            await rate_delivery(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 400
        assert "no transcript" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @patch("app.api.preparation.DeliveryRatingService")
    async def test_rates_delivery_successfully(self, mock_rating_cls):
        user = _make_user(SubscriptionTier.PRO)
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="STAR draft.")
        attempt = _make_attempt(prep_id=prep.id, transcript="I did X then Y.")

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])
        session.commit = AsyncMock()

        mock_rating_svc = MagicMock()
        mock_rating_cls.return_value = mock_rating_svc
        mock_rating = MagicMock()
        mock_rating.delivery_score = 88.5
        mock_rating.content_coverage = 90.0
        mock_rating.key_points = 85.0
        mock_rating.flow_structure = 87.0
        mock_rating.comparison_feedback = "Excellent delivery."
        mock_rating.strengths = ["clarity", "pace"]
        mock_rating.improvements = ["add more examples"]
        mock_rating_svc.rate_delivery = AsyncMock(return_value=mock_rating)

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=attempt.id)
        response = await rate_delivery(
            preparation_id=prep.id, request=req, current_user=user, session=session
        )
        assert response.delivery_score == 88.5
        assert "clarity" in response.strengths
        assert response.stage == "complete"
