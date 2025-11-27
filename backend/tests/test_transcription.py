"""Tests for transcription service and API."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.transcriber import Transcriber, TranscriptionResult


class TestTranscriber:
    """Tests for Transcriber service."""

    @pytest.fixture
    def transcriber(self):
        """Create Transcriber instance with mocked client."""
        with patch("app.ai.transcriber.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return Transcriber()

    def test_supported_formats(self, transcriber):
        """Test supported audio formats."""
        expected_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        assert transcriber.SUPPORTED_FORMATS == expected_formats

    def test_max_file_size(self, transcriber):
        """Test max file size limit."""
        assert transcriber.MAX_FILE_SIZE_MB == 25

    def test_estimate_cost(self, transcriber):
        """Test cost estimation."""
        # 1 minute = $0.006
        assert transcriber.estimate_cost(60) == 0.006

        # 5 minutes = $0.03
        assert transcriber.estimate_cost(300) == 0.03

        # 30 seconds = $0.003
        assert transcriber.estimate_cost(30) == 0.003

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found(self, transcriber):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            await transcriber.transcribe("/nonexistent/audio.mp3")

    @pytest.mark.asyncio
    async def test_transcribe_unsupported_format(self, transcriber, tmp_path):
        """Test error handling for unsupported format."""
        # Create a temp file with unsupported extension
        bad_file = tmp_path / "audio.txt"
        bad_file.write_bytes(b"not audio")

        with pytest.raises(ValueError) as exc_info:
            await transcriber.transcribe(str(bad_file))

        assert "Unsupported audio format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_file_too_large(self, transcriber, tmp_path):
        """Test error handling for file too large."""
        # Create a large temp file
        large_file = tmp_path / "large.mp3"

        # Write 26MB of data (over 25MB limit)
        with open(large_file, "wb") as f:
            f.write(b"0" * (26 * 1024 * 1024))

        with pytest.raises(ValueError) as exc_info:
            await transcriber.transcribe(str(large_file))

        assert "File too large" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_success(self, transcriber, tmp_path):
        """Test successful transcription."""
        # Create a small valid audio file
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"fake audio content")

        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.text = "This is the transcribed text."
        mock_response.language = "en"

        transcriber.client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        result = await transcriber.transcribe(str(audio_file))

        assert isinstance(result, TranscriptionResult)
        assert result.text == "This is the transcribed text."
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_transcribe_with_timestamps(self, transcriber, tmp_path):
        """Test transcription with timestamps."""
        audio_file = tmp_path / "audio.webm"
        audio_file.write_bytes(b"fake audio content")

        # Mock response with segments
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.5
        mock_segment.text = "Hello world"

        mock_response = MagicMock()
        mock_response.text = "Hello world"
        mock_response.duration = 2.5
        mock_response.language = "en"
        mock_response.segments = [mock_segment]

        transcriber.client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        result = await transcriber.transcribe(
            str(audio_file),
            include_timestamps=True,
        )

        assert result.duration_seconds == 2.5
        assert result.segments is not None
        assert len(result.segments) == 1
        assert result.segments[0]["start"] == 0.0
        assert result.segments[0]["end"] == 2.5

    @pytest.mark.asyncio
    async def test_transcribe_bytes(self, transcriber, tmp_path):
        """Test transcription from bytes."""
        audio_data = b"fake audio data"

        mock_response = MagicMock()
        mock_response.text = "Transcribed from bytes"
        mock_response.language = "en"

        transcriber.client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        result = await transcriber.transcribe_bytes(
            audio_data,
            filename="recording.webm",
        )

        assert result.text == "Transcribed from bytes"


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_basic_result(self):
        """Test basic result creation."""
        result = TranscriptionResult(text="Hello")
        assert result.text == "Hello"
        assert result.duration_seconds is None
        assert result.language is None
        assert result.segments is None

    def test_full_result(self):
        """Test result with all fields."""
        segments = [{"start": 0.0, "end": 1.0, "text": "Hello"}]
        result = TranscriptionResult(
            text="Hello",
            duration_seconds=1.0,
            language="en",
            segments=segments,
        )

        assert result.text == "Hello"
        assert result.duration_seconds == 1.0
        assert result.language == "en"
        assert result.segments == segments
