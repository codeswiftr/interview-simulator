"""Pure unit tests for feedback API route logic.

Covers:
- _verify_session_ownership(): found / not-found
- _verify_response_ownership(): found / not-found
- get_session_feedback(): returns feedback / raises 404 when missing
- get_all_session_feedbacks(): returns list (lines 148-154)
- get_response_feedback(): returns feedback / raises 404
- get_video_feedback(): returns feedback / raises 404 / feature-flag blocked (line 213)
- generate_response_feedback(): happy path (line 248) / ValueError -> 400
- generate_video_feedback(): happy path (lines 264-272) / ValueError -> 400 / feature-flag blocked
- generate_session_feedback(): happy path (lines 302-310) / ValueError -> 400
- get_session_processing_status(): happy path (lines 336-342)
- get_session_comparison(): all branches (lines 366-402)

No database required.  All dependencies are replaced with AsyncMock / MagicMock.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.feedback import (
    _verify_response_ownership,
    _verify_session_ownership,
    generate_response_feedback,
    generate_session_feedback,
    generate_video_feedback,
    get_all_session_feedbacks,
    get_response_feedback,
    get_session_comparison,
    get_session_feedback,
    get_session_processing_status,
    get_video_feedback,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _mock_session():
    """Return a lightweight AsyncMock that mimics an AsyncSession."""
    session = AsyncMock()
    session.exec = AsyncMock()
    return session


def _exec_returning(session, value):
    """Configure session.exec to return a result whose .first() gives *value*."""
    result = MagicMock()
    result.first.return_value = value
    session.exec.return_value = result
    return session


def _exec_all_returning(session, values):
    """Configure session.exec to return a result whose .all() gives *values*."""
    result = MagicMock()
    result.all.return_value = values
    session.exec.return_value = result
    return session


# ===========================================================================
# _verify_session_ownership
# ===========================================================================


class TestVerifySessionOwnership:
    @pytest.mark.asyncio
    async def test_returns_session_when_found(self):
        session = _mock_session()
        interview = MagicMock()
        _exec_returning(session, interview)

        found = await _verify_session_ownership(session, uuid4(), uuid4())
        assert found is interview

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        session = _mock_session()
        _exec_returning(session, None)

        with pytest.raises(HTTPException) as exc_info:
            await _verify_session_ownership(session, uuid4(), uuid4())
        assert exc_info.value.status_code == 404
        assert "not found or access denied" in str(exc_info.value.detail)


# ===========================================================================
# _verify_response_ownership
# ===========================================================================


class TestVerifyResponseOwnership:
    @pytest.mark.asyncio
    async def test_returns_response_when_found(self):
        session = _mock_session()
        response = MagicMock()
        _exec_returning(session, response)

        found = await _verify_response_ownership(session, uuid4(), uuid4())
        assert found is response

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        session = _mock_session()
        _exec_returning(session, None)

        with pytest.raises(HTTPException) as exc_info:
            await _verify_response_ownership(session, uuid4(), uuid4())
        assert exc_info.value.status_code == 404
        assert "not found or access denied" in str(exc_info.value.detail)


# ===========================================================================
# get_session_feedback
# ===========================================================================


class TestGetSessionFeedback:
    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_feedback(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedback = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=feedback)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_feedback(uuid4(), user, session)
        assert result is feedback

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_404_when_no_feedback(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=None)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await get_session_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 404
        assert "generate" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_session_ownership_is_called(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=MagicMock())
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        session_id = uuid4()
        await get_session_feedback(session_id, user, session)
        mock_verify.assert_awaited_once_with(session, session_id, user.id)


# ===========================================================================
# get_all_session_feedbacks  (lines 148-154)
# ===========================================================================


class TestGetAllSessionFeedbacks:
    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_list_of_feedbacks(self, mock_fs_cls, mock_verify):
        """Lines 148-154: verify ownership then return all feedbacks."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedbacks = [MagicMock(), MagicMock()]
        mock_fs = MagicMock()
        mock_fs.get_all_session_feedbacks = AsyncMock(return_value=feedbacks)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_all_session_feedbacks(uuid4(), user, session)
        assert result == feedbacks

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_empty_list_when_no_feedbacks(self, mock_fs_cls, mock_verify):
        """Empty list is returned without raising."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_all_session_feedbacks = AsyncMock(return_value=[])
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_all_session_feedbacks(uuid4(), user, session)
        assert result == []

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_ownership_called_with_correct_args(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_all_session_feedbacks = AsyncMock(return_value=[])
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        session_id = uuid4()
        await get_all_session_feedbacks(session_id, user, session)
        mock_verify.assert_awaited_once_with(session, session_id, user.id)


# ===========================================================================
# get_response_feedback
# ===========================================================================


class TestGetResponseFeedback:
    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_feedback(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedback = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_response_feedback = AsyncMock(return_value=feedback)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_response_feedback(uuid4(), user, session)
        assert result is feedback

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_404_when_no_feedback(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_response_feedback = AsyncMock(return_value=None)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await get_response_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 404


# ===========================================================================
# get_video_feedback  (lines 213: return feedback)
# ===========================================================================


class TestGetVideoFeedback:
    @pytest.mark.asyncio
    @patch("app.api.feedback.require_video_features_enabled")
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_video_feedback(self, mock_fs_cls, mock_verify, mock_ff):
        """Line 213: return feedback when found."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedback = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_video_feedback = AsyncMock(return_value=feedback)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_video_feedback(uuid4(), user, session)
        assert result is feedback

    @pytest.mark.asyncio
    @patch("app.api.feedback.require_video_features_enabled")
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_404_when_no_video_feedback(self, mock_fs_cls, mock_verify, mock_ff):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_video_feedback = AsyncMock(return_value=None)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await get_video_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 404
        assert "video feedback" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch(
        "app.api.feedback.require_video_features_enabled",
        side_effect=HTTPException(status_code=404, detail="Video review is not available"),
    )
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_404_when_feature_disabled(self, mock_fs_cls, mock_verify, mock_ff):
        """Feature flag blocks the endpoint before ownership check."""
        session = _mock_session()
        user = MagicMock()
        user.id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await get_video_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 404
        mock_verify.assert_not_awaited()


# ===========================================================================
# generate_response_feedback  (line 248: happy path)
# ===========================================================================


class TestGenerateResponseFeedback:
    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_feedback_on_success(self, mock_fs_cls, mock_verify):
        """Line 248: feedback is returned when generate_feedback succeeds."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedback = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_feedback = AsyncMock(return_value=feedback)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await generate_response_feedback(uuid4(), user, session)
        assert result is feedback

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_400_on_value_error(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_feedback = AsyncMock(side_effect=ValueError("no transcript"))
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await generate_response_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 400
        assert "no transcript" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_response_ownership_called(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_feedback = AsyncMock(return_value=MagicMock())
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        response_id = uuid4()
        await generate_response_feedback(response_id, user, session)
        mock_verify.assert_awaited_once_with(session, response_id, user.id)


# ===========================================================================
# generate_video_feedback  (lines 264-272)
# ===========================================================================


class TestGenerateVideoFeedback:
    @pytest.mark.asyncio
    @patch("app.api.feedback.require_video_features_enabled")
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_video_feedback_on_success(self, mock_fs_cls, mock_verify, mock_ff):
        """Lines 269-270: feedback returned when generate_video_feedback succeeds."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedback = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_video_feedback = AsyncMock(return_value=feedback)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await generate_video_feedback(uuid4(), user, session)
        assert result is feedback

    @pytest.mark.asyncio
    @patch("app.api.feedback.require_video_features_enabled")
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_400_on_value_error(self, mock_fs_cls, mock_verify, mock_ff):
        """Line 271-272: ValueError from service -> 400."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_video_feedback = AsyncMock(side_effect=ValueError("no video"))
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await generate_video_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 400
        assert "no video" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch(
        "app.api.feedback.require_video_features_enabled",
        side_effect=HTTPException(status_code=404, detail="Video review is not available"),
    )
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_404_when_feature_disabled(self, mock_fs_cls, mock_verify, mock_ff):
        """Line 264: feature flag blocks before ownership check."""
        session = _mock_session()
        user = MagicMock()
        user.id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await generate_video_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 404
        mock_verify.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.feedback.require_video_features_enabled")
    @patch("app.api.feedback._verify_response_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_response_ownership_called(self, mock_fs_cls, mock_verify, mock_ff):
        """Line 265: _verify_response_ownership called with correct args."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_video_feedback = AsyncMock(return_value=MagicMock())
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        response_id = uuid4()
        await generate_video_feedback(response_id, user, session)
        mock_verify.assert_awaited_once_with(session, response_id, user.id)


# ===========================================================================
# generate_session_feedback  (lines 302-310)
# ===========================================================================


class TestGenerateSessionFeedback:
    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_feedback_on_success(self, mock_fs_cls, mock_verify):
        """Lines 307-308: returns feedback when generate_session_feedback succeeds."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        feedback = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_session_feedback = AsyncMock(return_value=feedback)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await generate_session_feedback(uuid4(), user, session)
        assert result is feedback

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_400_on_value_error(self, mock_fs_cls, mock_verify):
        """Lines 309-310: ValueError from service -> 400."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_session_feedback = AsyncMock(side_effect=ValueError("no responses"))
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await generate_session_feedback(uuid4(), user, session)
        assert exc_info.value.status_code == 400
        assert "no responses" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_session_ownership_called(self, mock_fs_cls, mock_verify):
        """Line 302: _verify_session_ownership called with correct args."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.generate_session_feedback = AsyncMock(return_value=MagicMock())
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        session_id = uuid4()
        await generate_session_feedback(session_id, user, session)
        mock_verify.assert_awaited_once_with(session, session_id, user.id)


# ===========================================================================
# get_session_processing_status  (lines 336-342)
# ===========================================================================


class TestGetSessionProcessingStatus:
    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_summary_dict(self, mock_fs_cls, mock_verify):
        """Lines 339-342: returns processing summary from service."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        summary = {"pending": 2, "completed": 3, "all_processed": False}
        mock_fs = MagicMock()
        mock_fs.get_processing_summary = AsyncMock(return_value=summary)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_processing_status(uuid4(), user, session)
        assert result == summary

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_session_ownership_called(self, mock_fs_cls, mock_verify):
        """Line 336: _verify_session_ownership called."""
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_processing_summary = AsyncMock(return_value={})
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        session_id = uuid4()
        await get_session_processing_status(session_id, user, session)
        mock_verify.assert_awaited_once_with(session, session_id, user.id)

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_empty_summary_when_no_data(self, mock_fs_cls, mock_verify):
        session = _mock_session()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_processing_summary = AsyncMock(return_value={})
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_processing_status(uuid4(), user, session)
        assert result == {}


# ===========================================================================
# get_session_comparison  (lines 366-407)
# ===========================================================================


class TestGetSessionComparison:
    def _make_session_comparison_mocks(self, session_feedback, other_sessions=None):
        """Build the mocks needed by get_session_comparison."""
        db_session = AsyncMock()

        # First exec call (ownership check via _verify_session_ownership) happens
        # via patch, so session.exec is used only for other_sessions query.
        sessions_result = MagicMock()
        sessions_result.all.return_value = other_sessions or []
        db_session.exec.return_value = sessions_result

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)

        return db_session, mock_fs

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_raises_404_when_no_session_feedback(self, mock_fs_cls, mock_verify):
        """Lines 375-379: 404 when session has no feedback."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()
        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=None)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await get_session_comparison(uuid4(), user, db_session)
        assert exc_info.value.status_code == 404
        assert "feedback" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_comparison_no_other_sessions(self, mock_fs_cls, mock_verify):
        """Lines 388-406: no other sessions -> average_score None, no improvement %."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        session_feedback = MagicMock()
        session_feedback.overall_score = 75.0

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)
        mock_fs_cls.return_value = mock_fs

        # No other sessions
        sessions_result = MagicMock()
        sessions_result.all.return_value = []
        db_session.exec.return_value = sessions_result

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_comparison(uuid4(), user, db_session)

        assert result["session_score"] == 75.0
        assert result["average_score"] is None
        assert result["improvement_percent"] is None
        assert result["sessions_compared"] == 0

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_returns_comparison_with_other_sessions(self, mock_fs_cls, mock_verify):
        """Lines 392-400: average computed, improvement_percent calculated."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        session_feedback = MagicMock()
        session_feedback.overall_score = 80.0

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)
        mock_fs_cls.return_value = mock_fs

        # Build two other sessions with scores
        other1 = MagicMock()
        other1.overall_score = 60.0
        other2 = MagicMock()
        other2.overall_score = 70.0

        sessions_result = MagicMock()
        sessions_result.all.return_value = [other1, other2]
        db_session.exec.return_value = sessions_result

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_comparison(uuid4(), user, db_session)

        assert result["session_score"] == 80.0
        assert result["average_score"] == 65.0  # (60 + 70) / 2
        # improvement = ((80 - 65) / 65) * 100 = 23.1
        assert result["improvement_percent"] == pytest.approx(23.1, abs=0.1)
        assert result["sessions_compared"] == 2

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_sessions_with_none_score_are_excluded(self, mock_fs_cls, mock_verify):
        """Line 392: sessions with overall_score=None are excluded from average."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        session_feedback = MagicMock()
        session_feedback.overall_score = 90.0

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)
        mock_fs_cls.return_value = mock_fs

        # One session with a score, one without
        other_with_score = MagicMock()
        other_with_score.overall_score = 50.0
        other_without_score = MagicMock()
        other_without_score.overall_score = None

        sessions_result = MagicMock()
        sessions_result.all.return_value = [other_with_score, other_without_score]
        db_session.exec.return_value = sessions_result

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_comparison(uuid4(), user, db_session)

        # Only one session's score contributes
        assert result["average_score"] == 50.0
        assert result["sessions_compared"] == 1

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_no_improvement_when_average_is_zero(self, mock_fs_cls, mock_verify):
        """Line 397: improvement_percent is None when average_score == 0.

        The source evaluates ``round(average_score, 1) if average_score else None``
        on line 404, so an average of 0.0 (falsy) renders as None in the response.
        The guard on line 397 also prevents division-by-zero, so improvement_percent
        is None for the same reason.
        """
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        session_feedback = MagicMock()
        session_feedback.overall_score = 50.0

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)
        mock_fs_cls.return_value = mock_fs

        # Other session with 0 score — both average_score and improvement_percent
        # will be None because 0.0 is falsy in the conditional expression on line 404.
        other = MagicMock()
        other.overall_score = 0.0

        sessions_result = MagicMock()
        sessions_result.all.return_value = [other]
        db_session.exec.return_value = sessions_result

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_comparison(uuid4(), user, db_session)

        # average_score of 0.0 renders as None due to the falsy guard in line 404
        assert result["average_score"] is None
        assert result["improvement_percent"] is None
        assert result["sessions_compared"] == 1

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_verify_session_ownership_called(self, mock_fs_cls, mock_verify):
        """Line 369: _verify_session_ownership called with correct args."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=None)
        mock_fs_cls.return_value = mock_fs

        user = MagicMock()
        user.id = uuid4()
        session_id = uuid4()

        with pytest.raises(HTTPException):
            await get_session_comparison(session_id, user, db_session)

        mock_verify.assert_awaited_once_with(db_session, session_id, user.id)

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_session_score_is_rounded(self, mock_fs_cls, mock_verify):
        """Line 403: session_score is rounded to 1 decimal place."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        session_feedback = MagicMock()
        session_feedback.overall_score = 75.567

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)
        mock_fs_cls.return_value = mock_fs

        sessions_result = MagicMock()
        sessions_result.all.return_value = []
        db_session.exec.return_value = sessions_result

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_comparison(uuid4(), user, db_session)

        assert result["session_score"] == 75.6

    @pytest.mark.asyncio
    @patch("app.api.feedback._verify_session_ownership", new_callable=AsyncMock)
    @patch("app.api.feedback.FeedbackService")
    async def test_average_score_is_rounded(self, mock_fs_cls, mock_verify):
        """Line 404: average_score is rounded to 1 decimal place."""
        db_session = AsyncMock()
        mock_verify.return_value = MagicMock()

        session_feedback = MagicMock()
        session_feedback.overall_score = 80.0

        mock_fs = MagicMock()
        mock_fs.get_session_feedback = AsyncMock(return_value=session_feedback)
        mock_fs_cls.return_value = mock_fs

        other = MagicMock()
        other.overall_score = 66.666

        sessions_result = MagicMock()
        sessions_result.all.return_value = [other]
        db_session.exec.return_value = sessions_result

        user = MagicMock()
        user.id = uuid4()
        result = await get_session_comparison(uuid4(), user, db_session)

        assert result["average_score"] == pytest.approx(66.7, abs=0.1)
