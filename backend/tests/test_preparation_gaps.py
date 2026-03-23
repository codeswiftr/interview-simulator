"""Unit tests for preparation.py — gap coverage.

Targets previously-untested code paths:

start_preparation  (100% new coverage)
    - question not found → 404
    - existing preparation for same user+question → return existing
    - new preparation created → 201 with new id

list_preparations  (gap coverage)
    - question lookup returns None → falls back to "Unknown question"
    - no preparations for user → empty list

get_preparation_state  (gap coverage)
    - preparation not found → 404
    - question lookup returns None → empty content / fallback fields

update_draft  (100% new coverage)
    - happy path — saves new draft content
    - preparation not found → 404
    - wrong user (preparation.user_id != current_user.id) → 404

All tests use unittest.mock only.  No real DB or network calls.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.preparation import (
    DraftUpdateRequest,
    PreparationStartRequest,
    get_preparation_state,
    list_preparations,
    start_preparation,
    update_draft,
)
from app.models.preparation import (
    AnswerPreparation,
    PreparationStage,
)
from app.models.user import SubscriptionTier

# ---------------------------------------------------------------------------
# Shared helpers  (mirror the patterns from test_preparation_api_unit.py)
# ---------------------------------------------------------------------------


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
    question_id=None,
):
    prep = MagicMock(spec=AnswerPreparation)
    prep.id = prep_id or uuid4()
    prep.user_id = user_id or uuid4()
    prep.question_id = question_id or uuid4()
    prep.stage = stage
    prep.draft_answer = draft
    prep.created_at = datetime.now(UTC)
    prep.updated_at = datetime.now(UTC)
    return prep


def _make_question(content="Tell me about a challenging project."):
    q = MagicMock()
    q.id = uuid4()
    q.content = content
    q.category = "behavioral"
    q.difficulty = "medium"
    q.company_tags = []
    return q


def _make_session_single_result(return_value):
    """Return a session whose .exec() always yields the same MagicMock result."""
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = return_value
    session.exec = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# start_preparation
# ---------------------------------------------------------------------------


class TestStartPreparation:
    @pytest.mark.asyncio
    async def test_question_not_found_raises_404(self):
        """When the question does not exist, start_preparation raises HTTP 404."""
        user = _make_user()
        question_id = uuid4()
        request = PreparationStartRequest(question_id=question_id)

        session = _make_session_single_result(None)  # question lookup → None

        with pytest.raises(HTTPException) as exc_info:
            await start_preparation(request=request, current_user=user, session=session)

        assert exc_info.value.status_code == 404
        assert "Question not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_existing_preparation_returns_existing(self):
        """When a preparation already exists for user+question, return it instead of creating."""
        user = _make_user()
        question = _make_question()
        existing_prep = _make_preparation(
            user_id=user.id,
            stage=PreparationStage.DRAFT,
            question_id=question.id,
        )
        request = PreparationStartRequest(question_id=question.id)

        # First exec call → question result; second exec call → existing preparation result
        session = AsyncMock()
        question_result = MagicMock()
        question_result.first.return_value = question
        existing_result = MagicMock()
        existing_result.first.return_value = existing_prep
        session.exec = AsyncMock(side_effect=[question_result, existing_result])
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        response = await start_preparation(request=request, current_user=user, session=session)

        assert response.preparation_id == existing_prep.id
        assert "Resuming" in response.message
        # No new row should have been added
        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_preparation_returns_id(self):
        """Happy path — new preparation is created and the new id is returned."""
        user = _make_user()
        question = _make_question()
        request = PreparationStartRequest(question_id=question.id)

        # After session.refresh the preparation will have an id set on it.
        # We simulate this by configuring refresh to assign an id via side_effect.
        created_prep = _make_preparation(user_id=user.id, stage=PreparationStage.DETECTIVE)

        session = AsyncMock()
        question_result = MagicMock()
        question_result.first.return_value = question
        no_existing_result = MagicMock()
        no_existing_result.first.return_value = None  # no existing preparation
        session.exec = AsyncMock(side_effect=[question_result, no_existing_result])
        session.add = MagicMock()
        session.commit = AsyncMock()

        # refresh will be called on the newly-created AnswerPreparation object.
        # We capture the object passed to add() to inject our id, simulating DB assignment.
        captured = {}

        def _capture_add(obj):
            captured["prep"] = obj
            obj.id = created_prep.id
            obj.stage = PreparationStage.DETECTIVE

        session.add.side_effect = _capture_add
        session.refresh = AsyncMock()

        response = await start_preparation(request=request, current_user=user, session=session)

        session.add.assert_called_once()
        session.commit.assert_called_once()
        assert response.preparation_id == created_prep.id
        assert response.stage == "detective"
        assert "started" in response.message.lower()


# ---------------------------------------------------------------------------
# list_preparations
# ---------------------------------------------------------------------------


class TestListPreparations:
    @pytest.mark.asyncio
    async def test_returns_empty_when_none(self):
        """When a user has no preparations, the response list is empty."""
        user = _make_user()

        session = AsyncMock()
        preps_result = MagicMock()
        preps_result.all.return_value = []
        session.exec = AsyncMock(return_value=preps_result)

        response = await list_preparations(current_user=user, session=session)

        assert response.preparations == []

    @pytest.mark.asyncio
    async def test_question_not_found_uses_fallback_content(self):
        """When a question lookup returns None, item.question_content is 'Unknown question'."""
        user = _make_user()
        prep = _make_preparation(user_id=user.id)

        session = AsyncMock()
        # First exec → list of preparations
        preps_result = MagicMock()
        preps_result.all.return_value = [prep]
        # Second exec → question lookup returns None
        q_result = MagicMock()
        q_result.first.return_value = None
        session.exec = AsyncMock(side_effect=[preps_result, q_result])

        response = await list_preparations(current_user=user, session=session)

        assert len(response.preparations) == 1
        assert response.preparations[0].question_content == "Unknown question"


# ---------------------------------------------------------------------------
# get_preparation_state
# ---------------------------------------------------------------------------


class TestGetPreparationState:
    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        """When preparation is not found (or belongs to another user), raises HTTP 404."""
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_preparation_state(
                preparation_id=uuid4(), current_user=user, session=session
            )

        assert exc_info.value.status_code == 404
        assert "Preparation not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_question_not_found_uses_fallback(self):
        """When question lookup returns None, question context uses preparation.question_id
        and empty content rather than raising an error."""
        user = _make_user()
        prep = _make_preparation(user_id=user.id, stage=PreparationStage.DRAFT, draft="My draft.")

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = None  # question missing from DB
        qna_result = MagicMock()
        qna_result.all.return_value = []
        attempts_result = MagicMock()
        attempts_result.all.return_value = []
        session.exec = AsyncMock(
            side_effect=[prep_result, q_result, qna_result, attempts_result]
        )

        state = await get_preparation_state(
            preparation_id=prep.id, current_user=user, session=session
        )

        # Falls back to preparation.question_id and empty string for content
        assert state.question.id == prep.question_id
        assert state.question.content == ""
        assert state.preparation_id == prep.id


# ---------------------------------------------------------------------------
# update_draft
# ---------------------------------------------------------------------------


class TestUpdateDraft:
    def _make_draft_request(self, text="Revised draft answer."):
        req = MagicMock(spec=DraftUpdateRequest)
        req.draft_answer = text
        return req

    @pytest.mark.asyncio
    async def test_saves_new_draft_content(self):
        """Happy path — draft is updated in DB and the new content is returned."""
        user = _make_user()
        prep = _make_preparation(
            user_id=user.id,
            stage=PreparationStage.PRACTICE,
            draft="Original draft.",
        )
        request = self._make_draft_request("Updated draft answer.")

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        session.exec = AsyncMock(return_value=prep_result)
        session.add = MagicMock()
        session.commit = AsyncMock()

        # After refresh, prep.draft_answer should reflect the new value.
        # We simulate this by updating the mock attribute on the side_effect of refresh.
        async def _apply_refresh(obj):
            obj.draft_answer = request.draft_answer

        session.refresh = AsyncMock(side_effect=_apply_refresh)

        response = await update_draft(
            preparation_id=prep.id,
            request=request,
            current_user=user,
            session=session,
        )

        session.commit.assert_called_once()
        session.refresh.assert_called_once()
        assert response.draft_answer == "Updated draft answer."

    @pytest.mark.asyncio
    async def test_preparation_not_found_raises_404(self):
        """When no matching preparation exists for user+id, raises HTTP 404."""
        user = _make_user()
        request = self._make_draft_request()

        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await update_draft(
                preparation_id=uuid4(),
                request=request,
                current_user=user,
                session=session,
            )

        assert exc_info.value.status_code == 404
        assert "Preparation not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_wrong_user_raises_404(self):
        """When the DB query filters by user_id, a mismatched user_id returns no row → 404.

        The query in update_draft uses BOTH preparation_id AND user_id as filters, so a
        preparation owned by another user will not be found.  We model this by making
        .first() return None, which is exactly what the ORM produces when user_id differs.
        """
        requesting_user = _make_user()
        other_user_id = uuid4()
        # The preparation exists in DB but belongs to a different user.
        # Because the ORM query filters on current_user.id, the result set is empty.
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None  # filtered out by user_id mismatch
        session.exec = AsyncMock(return_value=result)

        request = self._make_draft_request()

        with pytest.raises(HTTPException) as exc_info:
            await update_draft(
                preparation_id=uuid4(),
                request=request,
                current_user=requesting_user,
                session=session,
            )

        assert exc_info.value.status_code == 404
        # The error must not leak which user owns the preparation
        assert "access denied" in exc_info.value.detail.lower() or "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_draft_no_existing_draft_raises_400(self):
        """If no draft has been generated yet, update_draft raises HTTP 400."""
        user = _make_user()
        # draft_answer is None — draft was never generated
        prep = _make_preparation(user_id=user.id, stage=PreparationStage.DETECTIVE, draft=None)
        request = self._make_draft_request()

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        session.exec = AsyncMock(return_value=prep_result)

        with pytest.raises(HTTPException) as exc_info:
            await update_draft(
                preparation_id=prep.id,
                request=request,
                current_user=user,
                session=session,
            )

        assert exc_info.value.status_code == 400
        assert "draft" in exc_info.value.detail.lower()
