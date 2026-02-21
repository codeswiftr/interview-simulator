"""Comprehensive tests for audio transcription service.

Tests cover:
- OpenAI Whisper API integration
- Groq provider support
- Multiple audio format handling
- Error conditions and edge cases
- Timestamp and language detection
- Cost estimation
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.ai.transcriber import Transcriber, TranscriptionResult


class TestTranscriberInitialization:
    """Tests for transcriber initialization and provider selection."""

    def test_init_openai_provider(self):
        """Test transcriber initializes with OpenAI provider."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "openai"
            mock_settings.openai_api_key = "test-key"

            transcriber = Transcriber()

            assert transcriber.provider == "openai"
            assert transcriber.model == "whisper-1"

    def test_init_groq_provider(self):
        """Test transcriber initializes with Groq provider."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "groq"
            mock_settings.groq_api_key = "test-key"

            transcriber = Transcriber()

            assert transcriber.provider == "groq"
            assert transcriber.model == "whisper-large-v3"

    def test_supported_formats(self):
        """Test supported audio formats are defined."""
        transcriber = Transcriber()

        expected_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        assert transcriber.SUPPORTED_FORMATS == expected_formats

    def test_max_file_size_limit(self):
        """Test maximum file size limit is defined."""
        transcriber = Transcriber()

        assert transcriber.MAX_FILE_SIZE_MB == 25


class TestTranscribeFile:
    """Tests for transcribing audio files."""

    @pytest.fixture
    def transcriber(self):
        """Create transcriber instance."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "openai"
            mock_settings.openai_api_key = "test-key"
            return Transcriber()

    @pytest.fixture
    def mock_audio_file(self, tmp_path):
        """Create a mock audio file for testing."""
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_bytes(b"fake audio data" * 100)  # ~1.5KB file
        return audio_file

    @pytest.mark.asyncio
    async def test_transcribe_success(self, transcriber: Transcriber, mock_audio_file: Path):
        """Test successful transcription of audio file.

        Should:
        - Accept valid audio file
        - Call OpenAI API with correct parameters
        - Return transcription result
        """
        mock_response = MagicMock()
        mock_response.text = "This is a test transcription."
        mock_response.language = "en"

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ) as mock_create:
            result = await transcriber.transcribe(mock_audio_file)

            assert isinstance(result, TranscriptionResult)
            assert result.text == "This is a test transcription."
            assert result.language == "en"

            # Verify API called correctly
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["model"] == "whisper-1"
            assert call_kwargs["response_format"] == "json"

    @pytest.mark.asyncio
    async def test_transcribe_with_timestamps(
        self, transcriber: Transcriber, mock_audio_file: Path
    ):
        """Test transcription with timestamp segments.

        Should include word-level timestamps in response.
        """
        # Mock response with segments
        segment1 = MagicMock()
        segment1.start = 0.0
        segment1.end = 2.5
        segment1.text = "Hello there"

        segment2 = MagicMock()
        segment2.start = 2.5
        segment2.end = 5.0
        segment2.text = "How are you"

        mock_response = MagicMock()
        mock_response.text = "Hello there How are you"
        mock_response.duration = 5.0
        mock_response.language = "en"
        mock_response.segments = [segment1, segment2]

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe(mock_audio_file, include_timestamps=True)

            assert result.text == "Hello there How are you"
            assert result.duration_seconds == 5.0
            assert result.segments is not None
            assert len(result.segments) == 2
            assert result.segments[0]["text"] == "Hello there"
            assert result.segments[0]["start"] == 0.0
            assert result.segments[1]["end"] == 5.0

    @pytest.mark.asyncio
    async def test_transcribe_with_language_hint(
        self, transcriber: Transcriber, mock_audio_file: Path
    ):
        """Test transcription with language hint.

        Should pass language parameter to API.
        """
        mock_response = MagicMock()
        mock_response.text = "Hola mundo"
        mock_response.language = "es"

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ) as mock_create:
            result = await transcriber.transcribe(mock_audio_file, language="es")

            assert result.text == "Hola mundo"
            assert result.language == "es"

            # Verify language parameter passed
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["language"] == "es"

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found(self, transcriber: Transcriber):
        """Test transcription with non-existent file.

        Should raise FileNotFoundError.
        """
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            await transcriber.transcribe("/nonexistent/file.mp3")

    @pytest.mark.asyncio
    async def test_transcribe_unsupported_format(
        self, transcriber: Transcriber, tmp_path: Path
    ):
        """Test transcription with unsupported file format.

        Should raise ValueError with supported formats list.
        """
        unsupported_file = tmp_path / "test.flac"
        unsupported_file.write_bytes(b"audio data")

        with pytest.raises(ValueError, match="Unsupported audio format"):
            await transcriber.transcribe(unsupported_file)

    @pytest.mark.asyncio
    async def test_transcribe_file_too_large(self, transcriber: Transcriber, tmp_path: Path):
        """Test transcription with file exceeding size limit.

        Should raise ValueError with size information.
        """
        large_file = tmp_path / "large_audio.mp3"
        # Create file larger than 25MB
        large_file.write_bytes(b"x" * (26 * 1024 * 1024))

        with pytest.raises(ValueError, match="File too large"):
            await transcriber.transcribe(large_file)

    @pytest.mark.asyncio
    async def test_transcribe_api_error(self, transcriber: Transcriber, mock_audio_file: Path):
        """Test transcription when API returns error.

        Should log error and re-raise exception.
        """
        with patch.object(
            transcriber.client.audio.transcriptions,
            "create",
            side_effect=Exception("API rate limit exceeded"),
        ):
            with pytest.raises(Exception, match="API rate limit exceeded"):
                await transcriber.transcribe(mock_audio_file)

    @pytest.mark.asyncio
    async def test_transcribe_different_formats(self, transcriber: Transcriber, tmp_path: Path):
        """Test transcription accepts all supported formats."""
        mock_response = MagicMock()
        mock_response.text = "Test transcription"

        supported_formats = ["mp3", "wav", "webm", "m4a"]

        for fmt in supported_formats:
            audio_file = tmp_path / f"test.{fmt}"
            audio_file.write_bytes(b"audio data")

            with patch.object(
                transcriber.client.audio.transcriptions, "create", return_value=mock_response
            ):
                result = await transcriber.transcribe(audio_file)
                assert result.text == "Test transcription"


class TestTranscribeBytes:
    """Tests for transcribing audio from bytes."""

    @pytest.fixture
    def transcriber(self):
        """Create transcriber instance."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "openai"
            mock_settings.openai_api_key = "test-key"
            return Transcriber()

    @pytest.mark.asyncio
    async def test_transcribe_bytes_success(self, transcriber: Transcriber):
        """Test transcription from audio bytes.

        Should:
        - Write bytes to temp file
        - Transcribe temp file
        - Clean up temp file
        """
        audio_bytes = b"fake audio data" * 100
        mock_response = MagicMock()
        mock_response.text = "Transcription from bytes"
        mock_response.language = "en"

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe_bytes(audio_bytes, filename="audio.webm")

            assert result.text == "Transcription from bytes"
            assert result.language == "en"

    @pytest.mark.asyncio
    async def test_transcribe_bytes_with_extension(self, transcriber: Transcriber):
        """Test that filename extension is preserved for format detection."""
        audio_bytes = b"audio data"
        mock_response = MagicMock()
        mock_response.text = "Test"

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ) as mock_create:
            await transcriber.transcribe_bytes(audio_bytes, filename="recording.mp3")

            # Verify temp file had correct extension
            # (temp file name will be in file object passed to create)
            call_kwargs = mock_create.call_args.kwargs
            assert "file" in call_kwargs

    @pytest.mark.asyncio
    async def test_transcribe_bytes_default_extension(self, transcriber: Transcriber):
        """Test default extension when no filename provided."""
        audio_bytes = b"audio data"
        mock_response = MagicMock()
        mock_response.text = "Test"

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe_bytes(audio_bytes)

            assert result.text == "Test"

    @pytest.mark.asyncio
    async def test_transcribe_bytes_with_timestamps(self, transcriber: Transcriber):
        """Test bytes transcription with timestamps enabled."""
        audio_bytes = b"audio data"

        segment = MagicMock()
        segment.start = 0.0
        segment.end = 1.0
        segment.text = "Test"

        mock_response = MagicMock()
        mock_response.text = "Test"
        mock_response.segments = [segment]
        mock_response.duration = 1.0

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe_bytes(
                audio_bytes, filename="audio.webm", include_timestamps=True
            )

            assert result.segments is not None
            assert len(result.segments) == 1


class TestCostEstimation:
    """Tests for transcription cost estimation."""

    @pytest.fixture
    def transcriber(self):
        """Create transcriber instance."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "openai"
            mock_settings.openai_api_key = "test-key"
            return Transcriber()

    def test_estimate_cost_60_seconds(self, transcriber: Transcriber):
        """Test cost estimation for 60-second audio.

        Whisper charges $0.006 per minute, so 60s = $0.006.
        """
        cost = transcriber.estimate_cost(60.0)
        assert cost == pytest.approx(0.006, rel=1e-6)

    def test_estimate_cost_5_minutes(self, transcriber: Transcriber):
        """Test cost estimation for 5-minute audio.

        5 minutes = $0.03.
        """
        cost = transcriber.estimate_cost(300.0)
        assert cost == pytest.approx(0.03, rel=1e-6)

    def test_estimate_cost_30_seconds(self, transcriber: Transcriber):
        """Test cost estimation for 30-second audio.

        30 seconds = 0.5 minutes = $0.003.
        """
        cost = transcriber.estimate_cost(30.0)
        assert cost == pytest.approx(0.003, rel=1e-6)

    def test_estimate_cost_zero_duration(self, transcriber: Transcriber):
        """Test cost estimation for zero-duration audio."""
        cost = transcriber.estimate_cost(0.0)
        assert cost == 0.0


class TestMultipleProviders:
    """Tests for multiple transcription provider support."""

    @pytest.mark.asyncio
    async def test_groq_provider_base_url(self):
        """Test Groq provider uses correct base URL."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "groq"
            mock_settings.groq_api_key = "test-key"

            transcriber = Transcriber()

            # Verify Groq base URL is set
            assert "groq.com" in str(transcriber.client.base_url)

    @pytest.mark.asyncio
    async def test_openai_provider_base_url(self):
        """Test OpenAI provider uses correct base URL."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "openai"
            mock_settings.openai_api_key = "test-key"

            transcriber = Transcriber()

            # OpenAI client should use default base URL
            # (not Groq's custom URL)
            assert "groq.com" not in str(transcriber.client.base_url)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def transcriber(self):
        """Create transcriber instance."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.transcription_provider = "openai"
            mock_settings.openai_api_key = "test-key"
            return Transcriber()

    @pytest.mark.asyncio
    async def test_transcribe_empty_file(self, transcriber: Transcriber, tmp_path: Path):
        """Test transcription of empty audio file.

        API should handle this gracefully or return error.
        """
        empty_file = tmp_path / "empty.mp3"
        empty_file.write_bytes(b"")

        mock_response = MagicMock()
        mock_response.text = ""

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe(empty_file)
            assert result.text == ""

    @pytest.mark.asyncio
    async def test_transcribe_no_speech(self, transcriber: Transcriber, mock_audio_file: Path):
        """Test transcription of audio with no speech (silence).

        API should return empty or minimal text.
        """
        mock_response = MagicMock()
        mock_response.text = ""

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe(mock_audio_file)
            assert result.text == ""

    @pytest.mark.asyncio
    async def test_transcribe_very_long_audio(
        self, transcriber: Transcriber, tmp_path: Path
    ):
        """Test transcription of long audio file (near size limit).

        Should accept files up to 25MB.
        """
        # Create file just under 25MB limit
        large_file = tmp_path / "long_audio.mp3"
        large_file.write_bytes(b"x" * (24 * 1024 * 1024))

        mock_response = MagicMock()
        mock_response.text = "Long transcription..."

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe(large_file)
            assert result.text == "Long transcription..."

    @pytest.mark.asyncio
    async def test_transcribe_unicode_in_result(
        self, transcriber: Transcriber, mock_audio_file: Path
    ):
        """Test transcription with Unicode characters in result.

        Should handle international characters correctly.
        """
        mock_response = MagicMock()
        mock_response.text = "Hello 你好 مرحبا こんにちは"
        mock_response.language = "multi"

        with patch.object(
            transcriber.client.audio.transcriptions, "create", return_value=mock_response
        ):
            result = await transcriber.transcribe(mock_audio_file)
            assert result.text == "Hello 你好 مرحبا こんにちは"
