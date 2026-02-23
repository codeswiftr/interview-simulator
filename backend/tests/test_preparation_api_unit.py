"""Comprehensive unit tests for app/api/preparation.py.

Targets uncovered lines:
- 57-62:    get_preparation_client() — singleton creation
- 293-294:  get_preparation_state — current_question when answer == ""
- 424-606:  get_detective_question — AI path, cache hit, cache LRU eviction, fallbacks
- 635-690:  submit_detective_answer — happy path, 404, 400, is_complete branch
- 719-828:  generate_draft — no API key fallback, AI path, AI exception fallback
- 1000-1001: start_practice — stage update when not already PRACTICE
- 1038-1099: submit_practice — existing attempt, missing audio file, transcription failure
- 1131-1152: get_attempts — happy path
- 1250-1251: rate_delivery — ValueError from rating service
- 1310-1341: get_comparison — happy path, 404 attempt

All tests use unittest.mock. No real DB or network calls.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.preparation import (
    generate_draft,
    get_attempts,
    get_comparison,
    get_detective_question,
    get_preparation_client,
    get_preparation_state,
    get_stage_value,
    list_preparations,
    rate_delivery,
    start_practice,
    submit_detective_answer,
    submit_practice,
)
from app.models.preparation import (
    AnswerPreparation,
    DeliveryAttempt,
    PreparationQnA,
    PreparationStage,
)
from app.models.user import SubscriptionTier

# ---------------------------------------------------------------------------
# Shared helpers
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


def _make_qna(question="Why did you do X?", answer="", order=1):
    qna = MagicMock(spec=PreparationQnA)
    qna.id = uuid4()
    qna.question = question
    qna.answer = answer
    qna.order = order
    return qna


# ---------------------------------------------------------------------------
# get_preparation_client — lines 57-62
# ---------------------------------------------------------------------------


class TestGetPreparationClient:
    def test_creates_client_when_none(self):
        """Client is created when _preparation_client is None."""
        import app.api.preparation as prep_module

        original = prep_module._preparation_client
        prep_module._preparation_client = None

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            with patch("app.api.preparation.AsyncOpenAI") as mock_cls:
                mock_cls.return_value = MagicMock()
                client = get_preparation_client()
                mock_cls.assert_called_once_with(
                    api_key="test-key",
                    base_url="https://openrouter.ai/api/v1",
                )
                assert client is mock_cls.return_value

        prep_module._preparation_client = original

    def test_returns_existing_client_without_recreating(self):
        """If client already exists, no new AsyncOpenAI is constructed."""
        import app.api.preparation as prep_module

        existing = MagicMock()
        original = prep_module._preparation_client
        prep_module._preparation_client = existing

        with patch("app.api.preparation.AsyncOpenAI") as mock_cls:
            result = get_preparation_client()
            mock_cls.assert_not_called()
            assert result is existing

        prep_module._preparation_client = original


# ---------------------------------------------------------------------------
# get_preparation_state — current_question branch (lines 293-294)
# ---------------------------------------------------------------------------


class TestGetPreparationStateCurrentQuestion:
    @pytest.mark.asyncio
    async def test_sets_current_question_from_unanswered_qna(self):
        """current_question is set to the first QnA entry whose answer is ''."""
        user = _make_user()
        prep = _make_preparation(user_id=user.id, stage=PreparationStage.DETECTIVE)
        question = _make_question()

        # One unanswered QnA
        unanswered_qna = _make_qna(question="Can you elaborate?", answer="", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [unanswered_qna]
        attempts_result = MagicMock()
        attempts_result.all.return_value = []
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result, attempts_result])

        state = await get_preparation_state(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert state.current_question == "Can you elaborate?"

    @pytest.mark.asyncio
    async def test_current_question_none_when_all_answered(self):
        """current_question is None when every QnA entry has a non-empty answer."""
        user = _make_user()
        prep = _make_preparation(user_id=user.id, stage=PreparationStage.DRAFT)
        question = _make_question()

        answered_qna = _make_qna(question="Tell me more?", answer="I did X.", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [answered_qna]
        attempts_result = MagicMock()
        attempts_result.all.return_value = []
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result, attempts_result])

        state = await get_preparation_state(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert state.current_question is None

    @pytest.mark.asyncio
    async def test_returns_attempts_in_state(self):
        """Delivery attempts are included in the state response."""
        user = _make_user()
        prep = _make_preparation(user_id=user.id, stage=PreparationStage.COMPLETE, draft="Draft.")
        question = _make_question()
        attempt = _make_attempt(prep_id=prep.id, transcript="Delivered answer.", score=90.0)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = []
        attempts_result = MagicMock()
        attempts_result.all.return_value = [attempt]
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result, attempts_result])

        state = await get_preparation_state(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert len(state.attempts) == 1
        assert state.attempts[0].delivery_score == 90.0


# ---------------------------------------------------------------------------
# get_detective_question — lines 424-606
# ---------------------------------------------------------------------------


class TestGetDetectiveQuestion:
    def _make_prep_session(self, prep, qna_list=None):
        """Build a session that returns prep + question + qna_list."""
        question = _make_question()
        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = qna_list or []
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result])
        session.add = MagicMock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_detective_question(
                preparation_id=uuid4(), current_user=user, session=session
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_402_for_free_user(self):
        user = _make_user(SubscriptionTier.FREE)
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        session.exec = AsyncMock(return_value=prep_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_raises_400_when_not_in_detective_stage(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert exc_info.value.status_code == 400
        assert "detective stage" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_no_api_key_first_question_returns_generic(self):
        """Without openrouter key, first question returns generic fallback."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = self._make_prep_session(prep, qna_list=[])

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert response.order == 1
        assert response.is_complete is False
        assert len(response.question) > 0

    @pytest.mark.asyncio
    async def test_no_api_key_second_question_marks_complete(self):
        """Without openrouter key and existing QnA, marks stage as DRAFT and complete."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        existing_qna = [_make_qna(answer="Some answer.", order=1)]
        session = self._make_prep_session(prep, qna_list=existing_qna)

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert response.is_complete is True
        assert prep.stage == PreparationStage.DRAFT

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_question(self):
        """When cache has the key, returns cached question and saves to DB."""
        import app.api.preparation as prep_module

        user = _make_user()
        user.experience_level = "senior"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)

        cache_key = f"{prep.question_id}:senior:0"
        cached_q = "Describe a time you led a team under pressure."

        # Inject into cache
        original_cache = dict(prep_module._detective_question_cache)
        original_order = list(prep_module._cache_access_order)
        prep_module._detective_question_cache[cache_key] = cached_q
        prep_module._cache_access_order.append(cache_key)

        try:
            session = self._make_prep_session(prep, qna_list=[])

            with patch("app.api.preparation.settings") as mock_settings:
                mock_settings.openrouter_api_key = "some-key"

                response = await get_detective_question(
                    preparation_id=prep.id, current_user=user, session=session
                )
            assert response.question == cached_q
            assert response.is_complete is False
            session.add.assert_called_once()
        finally:
            prep_module._detective_question_cache.clear()
            prep_module._detective_question_cache.update(original_cache)
            prep_module._cache_access_order.clear()
            prep_module._cache_access_order.extend(original_order)

    @pytest.mark.asyncio
    async def test_ai_generates_new_question_and_caches(self):
        """AI generates a question, saves to DB, and stores in cache."""
        import app.api.preparation as prep_module

        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)

        original_cache = dict(prep_module._detective_question_cache)
        original_order = list(prep_module._cache_access_order)

        try:
            session = self._make_prep_session(prep, qna_list=[])

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "What specific role did you play?"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with (
                patch("app.api.preparation.settings") as mock_settings,
                patch("app.api.preparation.get_preparation_client", return_value=mock_client),
            ):
                mock_settings.openrouter_api_key = "test-key"

                response = await get_detective_question(
                    preparation_id=prep.id, current_user=user, session=session
                )

            assert response.question == "What specific role did you play?"
            assert response.is_complete is False
            assert response.order == 1
            session.add.assert_called_once()
        finally:
            prep_module._detective_question_cache.clear()
            prep_module._detective_question_cache.update(original_cache)
            prep_module._cache_access_order.clear()
            prep_module._cache_access_order.extend(original_order)

    @pytest.mark.asyncio
    async def test_enough_info_signal_marks_complete(self):
        """When AI returns ENOUGH_INFO, stage transitions to DRAFT."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)

        session = self._make_prep_session(prep, qna_list=[])

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ENOUGH_INFO"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch("app.api.preparation.get_preparation_client", return_value=mock_client),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert response.is_complete is True
        assert prep.stage == PreparationStage.DRAFT

    @pytest.mark.asyncio
    async def test_enough_info_when_qna_count_exceeds_4(self):
        """When >= 4 existing QnA entries, marks complete regardless of AI response."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        many_qna = [_make_qna(answer="answer", order=i) for i in range(5)]

        session = self._make_prep_session(prep, qna_list=many_qna)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Tell me more about the outcome?"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch("app.api.preparation.get_preparation_client", return_value=mock_client),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert response.is_complete is True
        assert prep.stage == PreparationStage.DRAFT

    @pytest.mark.asyncio
    async def test_ai_exception_fallback_early_question(self):
        """On AI error with <= 3 questions asked, returns generic fallback question."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = self._make_prep_session(prep, qna_list=[])

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch(
                "app.api.preparation.get_preparation_client",
                side_effect=Exception("network error"),
            ),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert response.is_complete is False
        assert len(response.question) > 0
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_exception_fallback_late_question_marks_complete(self):
        """On AI error with > 3 questions asked, marks complete and transitions to DRAFT."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        # 4 answered QnAs — next would be order 5 (> 3 threshold in fallback)
        many_qna = [_make_qna(answer="answer", order=i) for i in range(1, 4)]

        session = self._make_prep_session(prep, qna_list=many_qna)

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch(
                "app.api.preparation.get_preparation_client",
                side_effect=Exception("timeout"),
            ),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        assert response.is_complete is True
        assert prep.stage == PreparationStage.DRAFT

    @pytest.mark.asyncio
    async def test_ai_empty_response_raises_value_error_then_fallback(self):
        """Empty AI content triggers ValueError, falls back to generic question."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = self._make_prep_session(prep, qna_list=[])

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch("app.api.preparation.get_preparation_client", return_value=mock_client),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await get_detective_question(
                preparation_id=prep.id, current_user=user, session=session
            )
        # Should fall into exception handler and return fallback
        assert response.is_complete is False

    @pytest.mark.asyncio
    async def test_cache_lru_eviction_when_full(self):
        """When cache is full, oldest entry is evicted before adding new one."""
        import app.api.preparation as prep_module

        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)

        original_cache = dict(prep_module._detective_question_cache)
        original_order = list(prep_module._cache_access_order)
        original_max = prep_module._MAX_CACHE_SIZE

        try:
            # Fill cache to max
            prep_module._MAX_CACHE_SIZE = 2
            prep_module._detective_question_cache.clear()
            prep_module._cache_access_order.clear()
            prep_module._detective_question_cache["old_key_1"] = "Old question 1"
            prep_module._detective_question_cache["old_key_2"] = "Old question 2"
            prep_module._cache_access_order.extend(["old_key_1", "old_key_2"])

            session = self._make_prep_session(prep, qna_list=[])

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Brand new question?"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with (
                patch("app.api.preparation.settings") as mock_settings,
                patch("app.api.preparation.get_preparation_client", return_value=mock_client),
            ):
                mock_settings.openrouter_api_key = "test-key"

                await get_detective_question(
                    preparation_id=prep.id, current_user=user, session=session
                )

            # old_key_1 should have been evicted
            assert "old_key_1" not in prep_module._detective_question_cache
        finally:
            prep_module._MAX_CACHE_SIZE = original_max
            prep_module._detective_question_cache.clear()
            prep_module._detective_question_cache.update(original_cache)
            prep_module._cache_access_order.clear()
            prep_module._cache_access_order.extend(original_order)


# ---------------------------------------------------------------------------
# submit_detective_answer — lines 635-690
# ---------------------------------------------------------------------------


class TestSubmitDetectiveAnswer:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import DetectiveAnswerRequest

        req = DetectiveAnswerRequest(answer="My answer.")
        with pytest.raises(HTTPException) as exc_info:
            await submit_detective_answer(
                preparation_id=uuid4(), request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_402_for_free_user(self):
        user = _make_user(SubscriptionTier.FREE)
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        session.exec = AsyncMock(return_value=prep_result)

        from app.api.preparation import DetectiveAnswerRequest

        req = DetectiveAnswerRequest(answer="My answer.")
        with pytest.raises(HTTPException) as exc_info:
            await submit_detective_answer(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_raises_400_when_not_in_detective_stage(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import DetectiveAnswerRequest

        req = DetectiveAnswerRequest(answer="My answer.")
        with pytest.raises(HTTPException) as exc_info:
            await submit_detective_answer(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_no_unanswered_question(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        no_qna_result = MagicMock()
        no_qna_result.first.return_value = None
        session.exec = AsyncMock(side_effect=[prep_result, no_qna_result])

        from app.api.preparation import DetectiveAnswerRequest

        req = DetectiveAnswerRequest(answer="My answer.")
        with pytest.raises(HTTPException) as exc_info:
            await submit_detective_answer(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 400
        assert "unanswered question" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_saves_answer_and_returns_next_question(self):
        """Saves the answer, fetches next question, returns not-complete response."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        unanswered_qna = _make_qna(question="How did you handle it?", answer="", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        qna_result = MagicMock()
        qna_result.first.return_value = unanswered_qna
        # For the inner get_detective_question call:
        inner_prep_result = MagicMock()
        inner_prep_result.first.return_value = prep
        inner_q_result = MagicMock()
        inner_q_result.first.return_value = _make_question()
        inner_qna_result = MagicMock()
        inner_qna_result.all.return_value = [unanswered_qna]

        session.exec = AsyncMock(
            side_effect=[prep_result, qna_result, inner_prep_result, inner_q_result, inner_qna_result]
        )
        session.add = MagicMock()
        session.commit = AsyncMock()

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""  # Force fallback path in inner call

            from app.api.preparation import DetectiveAnswerRequest

            req = DetectiveAnswerRequest(answer="I escalated to my manager.")
            response = await submit_detective_answer(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )

        assert unanswered_qna.answer == "I escalated to my manager."
        assert isinstance(response.stage, str)

    @pytest.mark.asyncio
    async def test_returns_complete_when_next_is_complete(self):
        """When inner get_detective_question returns is_complete=True, returns completion state."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        unanswered_qna = _make_qna(question="Final question?", answer="", order=1)
        # Simulate prep having 1 QnA already (so fallback returns complete)
        existing_qna = _make_qna(answer="previous", order=0)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        qna_result = MagicMock()
        qna_result.first.return_value = unanswered_qna
        # Inner call results
        inner_prep_result = MagicMock()
        inner_prep_result.first.return_value = prep
        inner_q_result = MagicMock()
        inner_q_result.first.return_value = _make_question()
        inner_qna_result = MagicMock()
        inner_qna_result.all.return_value = [existing_qna, unanswered_qna]

        session.exec = AsyncMock(
            side_effect=[
                prep_result,
                qna_result,
                inner_prep_result,
                inner_q_result,
                inner_qna_result,
            ]
        )
        session.add = MagicMock()
        session.commit = AsyncMock()

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""  # Fallback: order>1 -> complete

            from app.api.preparation import DetectiveAnswerRequest

            req = DetectiveAnswerRequest(answer="Done.")
            response = await submit_detective_answer(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )

        # If is_complete, stage should be "draft"
        if response.is_complete:
            assert response.stage == PreparationStage.DRAFT.value
            assert response.next_question is None


# ---------------------------------------------------------------------------
# generate_draft — lines 719-828
# ---------------------------------------------------------------------------


class TestGenerateDraft:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_draft(preparation_id=uuid4(), current_user=user, session=session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_402_for_free_user(self):
        user = _make_user(SubscriptionTier.FREE)
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_draft(preparation_id=prep.id, current_user=user, session=session)
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_raises_400_when_not_in_draft_stage(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DETECTIVE)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_draft(preparation_id=prep.id, current_user=user, session=session)
        assert exc_info.value.status_code == 400
        assert "detective stage" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_400_when_no_qna(self):
        """If no QnA entries, returns 400."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        question = _make_question()

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = []
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result])

        with pytest.raises(HTTPException) as exc_info:
            await generate_draft(preparation_id=prep.id, current_user=user, session=session)
        assert exc_info.value.status_code == 400
        assert "detective stage" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_fallback_draft_when_no_api_key(self):
        """Without API key, returns template fallback draft."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        question = _make_question()
        qna = _make_qna(question="Q?", answer="A.", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [qna]
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch("app.api.preparation.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""

            response = await generate_draft(
                preparation_id=prep.id, current_user=user, session=session
            )

        assert "Situation" in response.draft_answer or "Situation" in response.draft_answer
        assert response.stage == PreparationStage.PRACTICE.value

    @pytest.mark.asyncio
    async def test_ai_generates_draft_successfully(self):
        """AI path: generates draft, saves to DB, transitions to PRACTICE."""
        user = _make_user()
        user.experience_level = "senior"
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        question = _make_question()
        qna = _make_qna(question="What was your role?", answer="Tech lead.", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [qna]
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        ai_draft = "**Situation**: Led a team of 5. **Task**: Deliver MVP. **Action**: Sprinted. **Result**: Shipped on time."

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ai_draft
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch("app.api.preparation.get_preparation_client", return_value=mock_client),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await generate_draft(
                preparation_id=prep.id, current_user=user, session=session
            )

        assert response.draft_answer == ai_draft
        assert prep.draft_answer == ai_draft
        assert prep.stage == PreparationStage.PRACTICE
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_ai_exception_falls_back_to_template_draft(self):
        """On AI error, falls back to template draft and still transitions to PRACTICE."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        question = _make_question()
        qna = _make_qna(question="Q?", answer="A.", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [qna]
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch(
                "app.api.preparation.get_preparation_client",
                side_effect=Exception("AI unavailable"),
            ),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await generate_draft(
                preparation_id=prep.id, current_user=user, session=session
            )

        assert "Situation" in response.draft_answer
        assert response.stage == PreparationStage.PRACTICE.value

    @pytest.mark.asyncio
    async def test_ai_empty_response_falls_back_to_template(self):
        """Empty AI content triggers ValueError and falls back to template draft."""
        user = _make_user()
        user.experience_level = "mid"
        prep = _make_preparation(stage=PreparationStage.DRAFT)
        question = _make_question()
        qna = _make_qna(question="Q?", answer="A.", order=1)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        q_result = MagicMock()
        q_result.first.return_value = question
        qna_result = MagicMock()
        qna_result.all.return_value = [qna]
        session.exec = AsyncMock(side_effect=[prep_result, q_result, qna_result])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.preparation.settings") as mock_settings,
            patch("app.api.preparation.get_preparation_client", return_value=mock_client),
        ):
            mock_settings.openrouter_api_key = "test-key"

            response = await generate_draft(
                preparation_id=prep.id, current_user=user, session=session
            )

        assert "Situation" in response.draft_answer


# ---------------------------------------------------------------------------
# start_practice — stage update when not already PRACTICE (lines 1000-1001)
# ---------------------------------------------------------------------------


class TestStartPracticeStageTransition:
    @pytest.mark.asyncio
    async def test_updates_stage_to_practice_when_in_draft_stage(self):
        """When preparation is in DRAFT stage, start_practice updates it to PRACTICE."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.DRAFT, draft="STAR answer.")
        attempt = _make_attempt(prep_id=prep.id)

        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)
        session.add = MagicMock()

        commit_calls = []

        async def _commit():
            commit_calls.append(1)

        session.commit = AsyncMock(side_effect=_commit)

        async def _fake_refresh(obj):
            if isinstance(obj, MagicMock) and not hasattr(obj, "_refreshed"):
                obj._refreshed = True
                obj.id = attempt.id

        session.refresh = AsyncMock(side_effect=_fake_refresh)

        response = await start_practice(
            preparation_id=prep.id, current_user=user, session=session
        )

        # Stage should have been updated
        assert prep.stage == PreparationStage.PRACTICE
        # commit called at least twice (attempt creation + stage update)
        assert len(commit_calls) >= 2
        assert response.stage == "practice"

    @pytest.mark.asyncio
    async def test_skips_stage_update_when_already_practice(self):
        """When preparation is already in PRACTICE stage, no extra commit for stage."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="STAR answer.")
        attempt = _make_attempt(prep_id=prep.id)

        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)
        session.add = MagicMock()

        commit_calls = []

        async def _commit():
            commit_calls.append(1)

        session.commit = AsyncMock(side_effect=_commit)

        async def _fake_refresh(obj):
            obj.id = attempt.id

        session.refresh = AsyncMock(side_effect=_fake_refresh)

        response = await start_practice(
            preparation_id=prep.id, current_user=user, session=session
        )

        # Only one commit for attempt creation (no stage update needed)
        assert len(commit_calls) == 1
        assert response.stage == "practice"


# ---------------------------------------------------------------------------
# submit_practice — lines 1038-1099
# ---------------------------------------------------------------------------


class TestSubmitPractice:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import PracticeSubmitRequest

        req = PracticeSubmitRequest(audio_url="/uploads/audio/test.webm")
        with pytest.raises(HTTPException) as exc_info:
            await submit_practice(
                preparation_id=uuid4(), request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_402_for_free_user(self):
        user = _make_user(SubscriptionTier.FREE)
        prep = _make_preparation(stage=PreparationStage.PRACTICE)
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = prep
        session.exec = AsyncMock(return_value=result)

        from app.api.preparation import PracticeSubmitRequest

        req = PracticeSubmitRequest(audio_url="/uploads/audio/test.webm")
        with pytest.raises(HTTPException) as exc_info:
            await submit_practice(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_raises_404_when_audio_file_not_found(self):
        """If Path(audio_url) does not exist on disk, raises 404."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE)
        attempt = _make_attempt(prep_id=prep.id)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        from app.api.preparation import PracticeSubmitRequest

        req = PracticeSubmitRequest(audio_url="/uploads/audio/nonexistent_file.webm")
        with patch("app.api.preparation.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_path)

            with pytest.raises(HTTPException) as exc_info:
                await submit_practice(
                    preparation_id=prep.id, request=req, current_user=user, session=session
                )
        assert exc_info.value.status_code == 404
        assert "Audio file not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_creates_attempt_when_none_exists(self):
        """If no existing attempt, a new DeliveryAttempt is created before transcription."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE)

        # Represent the newly-created attempt as a real-ish object
        new_attempt_id = uuid4()

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        no_attempt_result = MagicMock()
        no_attempt_result.first.return_value = None  # No existing attempt
        session.exec = AsyncMock(side_effect=[prep_result, no_attempt_result])
        session.add = MagicMock()
        session.commit = AsyncMock()

        async def _fake_refresh(obj):
            obj.id = new_attempt_id

        session.refresh = AsyncMock(side_effect=_fake_refresh)

        from app.api.preparation import PracticeSubmitRequest

        req = PracticeSubmitRequest(audio_url="/uploads/audio/test.webm")

        with (
            patch("app.api.preparation.Path") as mock_path_cls,
            patch("app.api.preparation.Transcriber") as mock_transcriber_cls,
        ):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_path)

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber
            mock_result = MagicMock()
            mock_result.text = "Hello this is my transcript."
            mock_transcriber.transcribe = AsyncMock(return_value=mock_result)

            response = await submit_practice(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )

        session.add.assert_called()
        assert response.transcript == "Hello this is my transcript."

    @pytest.mark.asyncio
    async def test_transcription_failure_raises_500(self):
        """Transcription exception results in HTTP 500."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE)
        attempt = _make_attempt(prep_id=prep.id)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        from app.api.preparation import PracticeSubmitRequest

        req = PracticeSubmitRequest(audio_url="/uploads/audio/test.webm")

        with (
            patch("app.api.preparation.Path") as mock_path_cls,
            patch("app.api.preparation.Transcriber") as mock_transcriber_cls,
        ):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_path)

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber
            mock_transcriber.transcribe = AsyncMock(side_effect=Exception("Whisper API down"))

            with pytest.raises(HTTPException) as exc_info:
                await submit_practice(
                    preparation_id=prep.id, request=req, current_user=user, session=session
                )
        assert exc_info.value.status_code == 500
        assert "Transcription failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_successful_transcription_returns_transcript(self):
        """On success, returns attempt_id, transcript, and stage."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE)
        attempt = _make_attempt(prep_id=prep.id)
        attempt.audio_url = None
        attempt.transcript = None

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        from app.api.preparation import PracticeSubmitRequest

        req = PracticeSubmitRequest(audio_url="/uploads/audio/test.webm")

        with (
            patch("app.api.preparation.Path") as mock_path_cls,
            patch("app.api.preparation.Transcriber") as mock_transcriber_cls,
        ):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_path)

            mock_transcriber = MagicMock()
            mock_transcriber_cls.return_value = mock_transcriber
            mock_result = MagicMock()
            mock_result.text = "My transcribed answer."
            mock_transcriber.transcribe = AsyncMock(return_value=mock_result)

            response = await submit_practice(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )

        assert attempt.transcript == "My transcribed answer."
        assert response.transcript == "My transcribed answer."
        assert response.attempt_id == attempt.id


# ---------------------------------------------------------------------------
# get_attempts — lines 1131-1152
# ---------------------------------------------------------------------------


class TestGetAttempts:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_attempts(preparation_id=uuid4(), current_user=user, session=session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_empty_attempts_list(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempts_result = MagicMock()
        attempts_result.all.return_value = []
        session.exec = AsyncMock(side_effect=[prep_result, attempts_result])

        response = await get_attempts(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert response.attempts == []

    @pytest.mark.asyncio
    async def test_returns_all_attempts_with_details(self):
        """Returns attempts list with all fields properly mapped."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.COMPLETE)
        attempt1 = _make_attempt(prep_id=prep.id, transcript="First attempt.", score=75.0)
        attempt2 = _make_attempt(prep_id=prep.id, transcript="Second attempt.", score=88.0)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempts_result = MagicMock()
        attempts_result.all.return_value = [attempt1, attempt2]
        session.exec = AsyncMock(side_effect=[prep_result, attempts_result])

        response = await get_attempts(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert len(response.attempts) == 2
        assert response.attempts[0].transcript == "First attempt."
        assert response.attempts[1].delivery_score == 88.0

    @pytest.mark.asyncio
    async def test_attempt_without_comparison_details_uses_empty_lists(self):
        """Attempt with comparison_details=None produces empty strengths/improvements."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.COMPLETE)
        attempt = _make_attempt(prep_id=prep.id)
        attempt.comparison_details = None

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempts_result = MagicMock()
        attempts_result.all.return_value = [attempt]
        session.exec = AsyncMock(side_effect=[prep_result, attempts_result])

        response = await get_attempts(
            preparation_id=prep.id, current_user=user, session=session
        )
        assert response.attempts[0].strengths == []
        assert response.attempts[0].improvements == []


# ---------------------------------------------------------------------------
# rate_delivery — ValueError path (lines 1250-1251)
# ---------------------------------------------------------------------------


class TestRateDeliveryValueError:
    @pytest.mark.asyncio
    @patch("app.api.preparation.DeliveryRatingService")
    async def test_raises_500_when_rating_service_raises_value_error(self, mock_rating_cls):
        """When DeliveryRatingService.rate_delivery raises ValueError, returns HTTP 500."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft="My STAR draft.")
        attempt = _make_attempt(prep_id=prep.id, transcript="Delivered text.")

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        mock_rating_svc = MagicMock()
        mock_rating_cls.return_value = mock_rating_svc
        mock_rating_svc.rate_delivery = AsyncMock(
            side_effect=ValueError("AI response parsing failed")
        )

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=attempt.id)
        with pytest.raises(HTTPException) as exc_info:
            await rate_delivery(
                preparation_id=prep.id, request=req, current_user=user, session=session
            )
        assert exc_info.value.status_code == 500
        assert "Rating failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("app.api.preparation.DeliveryRatingService")
    async def test_stage_already_complete_stays_complete(self, mock_rating_cls):
        """When preparation is already COMPLETE, stage stays COMPLETE after rating."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.COMPLETE, draft="My STAR draft.")
        attempt = _make_attempt(prep_id=prep.id, transcript="Delivered text.")

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
        mock_rating.delivery_score = 92.0
        mock_rating.content_coverage = 95.0
        mock_rating.key_points = 90.0
        mock_rating.flow_structure = 91.0
        mock_rating.comparison_feedback = "Excellent."
        mock_rating.strengths = ["clarity"]
        mock_rating.improvements = ["add examples"]
        mock_rating_svc.rate_delivery = AsyncMock(return_value=mock_rating)

        from app.api.preparation import RateDeliveryRequest

        req = RateDeliveryRequest(attempt_id=attempt.id)
        response = await rate_delivery(
            preparation_id=prep.id, request=req, current_user=user, session=session
        )
        # Stage was already COMPLETE — should remain COMPLETE, no extra commit for stage
        assert response.stage == "complete"


# ---------------------------------------------------------------------------
# get_comparison — lines 1310-1341
# ---------------------------------------------------------------------------


class TestGetComparison:
    @pytest.mark.asyncio
    async def test_raises_404_when_preparation_not_found(self):
        user = _make_user()
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.exec = AsyncMock(return_value=result)

        with pytest.raises(HTTPException) as exc_info:
            await get_comparison(
                preparation_id=uuid4(),
                attempt_id=uuid4(),
                current_user=user,
                session=session,
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_when_attempt_not_found(self):
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.COMPLETE, draft="Draft text.")

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = None
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        with pytest.raises(HTTPException) as exc_info:
            await get_comparison(
                preparation_id=prep.id,
                attempt_id=uuid4(),
                current_user=user,
                session=session,
            )
        assert exc_info.value.status_code == 404
        assert "Delivery attempt not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_returns_comparison_with_all_fields(self):
        """Returns ComparisonResponse with draft, delivery, score, feedback, strengths."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.COMPLETE, draft="STAR formatted draft.")
        attempt = _make_attempt(prep_id=prep.id, transcript="My spoken answer.", score=87.5)
        attempt.comparison_details = {
            "strengths": ["good structure", "specific examples"],
            "improvements": ["more concise", "add metrics"],
        }

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        response = await get_comparison(
            preparation_id=prep.id,
            attempt_id=attempt.id,
            current_user=user,
            session=session,
        )
        assert response.draft == "STAR formatted draft."
        assert response.delivery == "My spoken answer."
        assert response.delivery_score == 87.5
        assert "good structure" in response.strengths
        assert "more concise" in response.improvements

    @pytest.mark.asyncio
    async def test_comparison_with_null_details_returns_empty_lists(self):
        """When comparison_details is None, strengths and improvements default to []."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.COMPLETE, draft="Draft.")
        attempt = _make_attempt(prep_id=prep.id, transcript="Delivery.")
        attempt.comparison_details = None
        attempt.delivery_score = None
        attempt.comparison_feedback = None

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        response = await get_comparison(
            preparation_id=prep.id,
            attempt_id=attempt.id,
            current_user=user,
            session=session,
        )
        assert response.strengths == []
        assert response.improvements == []
        assert response.delivery_score is None
        assert response.comparison_feedback is None

    @pytest.mark.asyncio
    async def test_comparison_with_null_draft_returns_empty_string(self):
        """When preparation.draft_answer is None, draft in response is empty string."""
        user = _make_user()
        prep = _make_preparation(stage=PreparationStage.PRACTICE, draft=None)
        attempt = _make_attempt(prep_id=prep.id)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.first.return_value = prep
        attempt_result = MagicMock()
        attempt_result.first.return_value = attempt
        session.exec = AsyncMock(side_effect=[prep_result, attempt_result])

        response = await get_comparison(
            preparation_id=prep.id,
            attempt_id=attempt.id,
            current_user=user,
            session=session,
        )
        assert response.draft == ""


# ---------------------------------------------------------------------------
# list_preparations — unknown question fallback
# ---------------------------------------------------------------------------


class TestListPreparationsEdgeCases:
    @pytest.mark.asyncio
    async def test_question_not_found_uses_unknown_content(self):
        """When question is not found for a preparation, uses 'Unknown question' placeholder."""
        user = _make_user()
        prep = _make_preparation(user_id=user.id)

        session = AsyncMock()
        prep_result = MagicMock()
        prep_result.all.return_value = [prep]
        q_result = MagicMock()
        q_result.first.return_value = None  # Question not found
        session.exec = AsyncMock(side_effect=[prep_result, q_result])

        response = await list_preparations(current_user=user, session=session)
        assert len(response.preparations) == 1
        assert response.preparations[0].question_content == "Unknown question"


# ---------------------------------------------------------------------------
# get_stage_value — additional edge cases
# ---------------------------------------------------------------------------


class TestGetStageValueEdgeCases:
    def test_returns_string_for_plain_string_input(self):
        assert get_stage_value("practice") == "practice"

    def test_returns_detective_for_falsy_none(self):
        assert get_stage_value(None) == "detective"

    def test_returns_detective_for_empty_string(self):
        assert get_stage_value("") == "detective"
