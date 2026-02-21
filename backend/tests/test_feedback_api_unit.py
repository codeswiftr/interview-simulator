"""Pure unit tests for feedback API route logic.

Tests ownership verification, session/response feedback retrieval, video feedback.
No database required.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.feedback import (
    _verify_response_ownership,
    _verify_session_ownership,
    generate_response_feedback,
    get_response_feedback,
    get_session_feedback,
    get_video_feedback,
)


def _mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    return session


class TestVerifySessionOwnership:
    @pytest.mark.asyncio
    async def test_returns_session_when_found(self):
        session = _mock_session()
        interview = MagicMock()
        result = MagicMock()
        result.first.return_value = interview
        session.exec.return_value = result

        found = await _verify_session_ownership(session, uuid4(), uuid4())
        assert found == interview

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await _verify_session_ownership(session, uuid4(), uuid4())
        assert exc_info.value.status_code == 404
        assert "not found or access denied" in str(exc_info.value.detail)


class TestVerifyResponseOwnership:
    @pytest.mark.asyncio
    async def test_returns_response_when_found(self):
        session = _mock_session()
        response = MagicMock()
        result = MagicMock()
        result.first.return_value = response
        session.exec.return_value = result

        found = await _verify_response_ownership(session, uuid4(), uuid4())
        assert found == response

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        session = _mock_session()
        result = MagicMock()
        result.first.return_value = None
        session.exec.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await _verify_response_ownership(session, uuid4(), uuid4())
        assert exc_info.value.status_code == 404


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
        assert result == feedback

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
        assert result == feedback

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


class TestGetVideoFeedback:
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


class TestGenerateResponseFeedback:
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
