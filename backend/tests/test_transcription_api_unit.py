"""Pure unit tests for transcription API route logic.

Tests parameter validation, error paths, supported formats.
No external services required.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.transcription import TranscriptionError, TranscriptionResponse, transcribe_audio


class TestTranscriptionResponse:
    def test_basic_fields(self):
        resp = TranscriptionResponse(text="Hello world")
        assert resp.text == "Hello world"
        assert resp.duration_seconds is None
        assert resp.language is None
        assert resp.segments is None
        assert resp.estimated_cost is None

    def test_all_fields(self):
        resp = TranscriptionResponse(
            text="Test transcript",
            duration_seconds=60.5,
            language="en",
            segments=[{"start": 0, "end": 1, "text": "Test"}],
            estimated_cost=0.006,
        )
        assert resp.duration_seconds == 60.5
        assert resp.language == "en"
        assert len(resp.segments) == 1


class TestTranscriptionError:
    def test_fields(self):
        err = TranscriptionError(detail="File too large", error_type="size_limit")
        assert err.detail == "File too large"
        assert err.error_type == "size_limit"


class TestTranscribeAudio:
    @pytest.mark.asyncio
    async def test_no_filename_raises_400(self):
        file = MagicMock()
        file.filename = None
        user = MagicMock()
        user.id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(file=file, current_user=user)
        assert exc_info.value.status_code == 400
        assert "No filename" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_empty_filename_raises_400(self):
        file = MagicMock()
        file.filename = ""
        user = MagicMock()
        user.id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(file=file, current_user=user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_file_too_large_raises_413(self):
        file = MagicMock()
        file.filename = "test.webm"
        file.content_type = "audio/webm"
        # 30MB content (over 25MB limit)
        file.read = AsyncMock(return_value=b"x" * (30 * 1024 * 1024))
        user = MagicMock()
        user.id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(file=file, current_user=user)
        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    @patch("app.api.transcription.Transcriber")
    async def test_value_error_raises_422(self, mock_transcriber_cls):
        file = MagicMock()
        file.filename = "test.webm"
        file.content_type = "audio/webm"
        file.read = AsyncMock(return_value=b"x" * 1024)
        user = MagicMock()
        user.id = uuid4()

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe = AsyncMock(side_effect=ValueError("Unsupported format"))
        mock_transcriber_cls.return_value = mock_transcriber

        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(file=file, current_user=user)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.transcription.Transcriber")
    async def test_file_not_found_raises_400(self, mock_transcriber_cls):
        file = MagicMock()
        file.filename = "test.mp3"
        file.content_type = "audio/mp3"
        file.read = AsyncMock(return_value=b"x" * 1024)
        user = MagicMock()
        user.id = uuid4()

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe = AsyncMock(side_effect=FileNotFoundError("not found"))
        mock_transcriber_cls.return_value = mock_transcriber

        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(file=file, current_user=user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.transcription.Transcriber")
    async def test_generic_error_raises_500(self, mock_transcriber_cls):
        file = MagicMock()
        file.filename = "test.wav"
        file.content_type = "audio/wav"
        file.read = AsyncMock(return_value=b"x" * 1024)
        user = MagicMock()
        user.id = uuid4()

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe = AsyncMock(side_effect=RuntimeError("API down"))
        mock_transcriber_cls.return_value = mock_transcriber

        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(file=file, current_user=user)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch("app.api.transcription.Transcriber")
    async def test_successful_transcription(self, mock_transcriber_cls):
        file = MagicMock()
        file.filename = "test.webm"
        file.content_type = "audio/webm"
        file.read = AsyncMock(return_value=b"x" * 1024)
        user = MagicMock()
        user.id = uuid4()

        mock_result = MagicMock()
        mock_result.text = "Hello world"
        mock_result.duration_seconds = 5.0
        mock_result.language = "en"
        mock_result.segments = None

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe = AsyncMock(return_value=mock_result)
        mock_transcriber.estimate_cost.return_value = 0.0005
        mock_transcriber_cls.return_value = mock_transcriber

        result = await transcribe_audio(file=file, current_user=user)
        assert result.text == "Hello world"
        assert result.duration_seconds == 5.0
        assert result.estimated_cost == 0.0005
