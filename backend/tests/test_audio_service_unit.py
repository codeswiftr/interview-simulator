"""Unit tests for audio service (no database required)."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.ai.audio_analyzer import AudioMetrics
from app.ai.transcriber import TranscriptionResult
from app.services.audio_service import AudioService


class TestAudioServiceInit:
    """Tests for AudioService initialization."""

    def test_initialization_creates_transcriber(self):
        """Test that initialization creates a transcriber."""
        service = AudioService()
        assert service.transcriber is not None

    def test_initialization_creates_analyzer(self):
        """Test that initialization creates an analyzer."""
        service = AudioService()
        assert service.analyzer is not None


class TestProcessResponseAudio:
    """Tests for process_response_audio method."""

    @pytest.mark.asyncio
    async def test_raises_if_response_not_found(self):
        """Test that ValueError is raised if response not found."""
        service = AudioService()
        response_id = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="not found"):
            await service.process_response_audio(mock_session, response_id, "/path/to/audio.webm")

    @pytest.mark.asyncio
    async def test_raises_if_audio_file_not_found(self):
        """Test that ValueError is raised if audio file doesn't exist."""
        service = AudioService()
        response_id = uuid4()

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="Audio file not found"):
            await service.process_response_audio(
                mock_session, response_id, "/nonexistent/path/audio.webm"
            )

    @pytest.mark.asyncio
    async def test_processes_audio_successfully(self, tmp_path):
        """Test successful audio processing flow."""
        service = AudioService()
        response_id = uuid4()

        # Create temp audio file
        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake audio data")

        mock_response = MagicMock()
        mock_response.transcript = None
        mock_response.duration_seconds = None
        mock_response.word_count = None
        mock_response.filler_word_count = None

        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(
            text="This is a test transcript",
            duration_seconds=120.0,
            language="en",
        )

        mock_metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={"um": 2, "uh": 1},
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service, "analyze_audio", new_callable=AsyncMock, return_value=mock_metrics
            ),
        ):
            transcript, metrics = await service.process_response_audio(
                mock_session, response_id, str(audio_file)
            )

        assert transcript == "This is a test transcript"
        assert metrics.speech_rate_wpm == 130.0
        assert mock_response.transcript == "This is a test transcript"
        assert mock_response.word_count == 5
        assert mock_response.filler_word_count == 3  # um(2) + uh(1)

    @pytest.mark.asyncio
    async def test_updates_duration_from_transcription(self, tmp_path):
        """Test that duration is updated from transcription result."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake audio data")

        mock_response = MagicMock()
        mock_response.transcript = None
        mock_response.duration_seconds = 0

        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(
            text="Test",
            duration_seconds=180.5,
        )

        mock_metrics = AudioMetrics(
            speech_rate_wpm=100.0,
            filler_words={},
            volume_consistency=80.0,
            confidence_score=70.0,
        )

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service, "analyze_audio", new_callable=AsyncMock, return_value=mock_metrics
            ),
        ):
            await service.process_response_audio(mock_session, response_id, str(audio_file))

        assert mock_response.duration_seconds == 180  # Truncated to int

    @pytest.mark.asyncio
    async def test_handles_transcription_exception(self, tmp_path, caplog):
        """Test that transcription exceptions are wrapped in ValueError."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake audio data")

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        with (
            patch.object(
                service,
                "transcribe_audio",
                new_callable=AsyncMock,
                side_effect=ValueError("Transcription failed"),
            ),
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="Failed to process audio"),
        ):
            await service.process_response_audio(mock_session, response_id, str(audio_file))

        assert "failed" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_handles_analysis_exception(self, tmp_path, caplog):
        """Test that analysis exceptions are wrapped in ValueError."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake audio data")

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(text="Test", duration_seconds=60.0)

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service,
                "analyze_audio",
                new_callable=AsyncMock,
                side_effect=ValueError("Analysis failed"),
            ),
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="Failed to process audio"),
        ):
            await service.process_response_audio(mock_session, response_id, str(audio_file))


class TestTranscribeAudio:
    """Tests for transcribe_audio method."""

    @pytest.mark.asyncio
    async def test_transcribes_successfully(self):
        """Test successful transcription."""
        service = AudioService()

        mock_result = TranscriptionResult(
            text="Hello world",
            duration_seconds=5.0,
            language="en",
        )

        with patch.object(
            service.transcriber, "transcribe", new_callable=AsyncMock, return_value=mock_result
        ):
            result = await service.transcribe_audio("/path/to/audio.webm")

        assert result.text == "Hello world"
        assert result.duration_seconds == 5.0

    @pytest.mark.asyncio
    async def test_raises_value_error_on_failure(self, caplog):
        """Test that transcription failures raise ValueError."""
        service = AudioService()

        with (
            patch.object(
                service.transcriber,
                "transcribe",
                new_callable=AsyncMock,
                side_effect=Exception("API error"),
            ),
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="Transcription failed"),
        ):
            await service.transcribe_audio("/path/to/audio.webm")

        assert "Transcription failed" in caplog.text

    @pytest.mark.asyncio
    async def test_passes_correct_parameters(self):
        """Test that transcribe is called with correct parameters."""
        service = AudioService()

        with patch.object(
            service.transcriber, "transcribe", new_callable=AsyncMock
        ) as mock_transcribe:
            mock_transcribe.return_value = TranscriptionResult(text="Test")

            await service.transcribe_audio("/path/to/audio.webm")

            mock_transcribe.assert_called_once_with(
                "/path/to/audio.webm",
                include_timestamps=False,
            )


class TestAnalyzeAudio:
    """Tests for analyze_audio method."""

    @pytest.mark.asyncio
    async def test_analyzes_successfully(self):
        """Test successful audio analysis."""
        service = AudioService()

        mock_metrics = AudioMetrics(
            speech_rate_wpm=140.0,
            filler_words={"um": 3},
            volume_consistency=90.0,
            confidence_score=85.0,
        )

        with patch.object(
            service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics
        ):
            result = await service.analyze_audio("/path/to/audio.webm", "Some transcript")

        assert result.speech_rate_wpm == 140.0
        assert result.filler_words == {"um": 3}

    @pytest.mark.asyncio
    async def test_raises_value_error_on_failure(self, caplog):
        """Test that analysis failures raise ValueError."""
        service = AudioService()

        with (
            patch.object(
                service.analyzer,
                "analyze",
                new_callable=AsyncMock,
                side_effect=Exception("Analysis error"),
            ),
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="Audio analysis failed"),
        ):
            await service.analyze_audio("/path/to/audio.webm", "transcript")

        assert "Audio analysis failed" in caplog.text

    @pytest.mark.asyncio
    async def test_handles_none_transcript(self):
        """Test that None transcript is handled."""
        service = AudioService()

        mock_metrics = AudioMetrics(
            speech_rate_wpm=100.0,
            filler_words={},
            volume_consistency=80.0,
            confidence_score=70.0,
        )

        with patch.object(
            service.analyzer, "analyze", new_callable=AsyncMock, return_value=mock_metrics
        ):
            result = await service.analyze_audio("/path/to/audio.webm", None)

        assert result is not None


class TestSaveAudioFeedback:
    """Tests for save_audio_feedback method."""

    @pytest.mark.asyncio
    async def test_prevents_duplicate_feedback(self):
        """Test that duplicate feedback is prevented."""
        service = AudioService()
        response_id = uuid4()

        # Mock existing feedback
        mock_existing = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_existing

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)

        metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={},
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.save_audio_feedback(mock_session, response_id, metrics)

    @pytest.mark.asyncio
    async def test_creates_feedback_successfully(self):
        """Test successful feedback creation."""
        service = AudioService()
        response_id = uuid4()

        # First call returns None (no existing), second returns response
        call_count = 0
        mock_response = MagicMock()
        mock_response.word_count = 100

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = None  # No existing feedback
            else:
                mock_result.first.return_value = mock_response  # Response for word count
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={"um": 2},
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        # Mock the score calculation methods
        with (
            patch.object(service.analyzer, "calculate_speech_rate_score", return_value=100.0),
            patch.object(service.analyzer, "calculate_filler_score", return_value=90.0),
        ):
            feedback = await service.save_audio_feedback(mock_session, response_id, metrics)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert feedback is not None

    @pytest.mark.asyncio
    async def test_uses_default_word_count_when_none(self):
        """Test that default word count (100) is used when response has None."""
        service = AudioService()
        response_id = uuid4()

        call_count = 0
        mock_response = MagicMock()
        mock_response.word_count = None

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = None
            else:
                mock_result.first.return_value = mock_response
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={"um": 5},  # 5 fillers
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        # The default word count of 100 should be used
        with (
            patch.object(service.analyzer, "calculate_speech_rate_score", return_value=100.0),
            patch.object(
                service.analyzer, "calculate_filler_score", return_value=85.0
            ) as mock_filler,
        ):
            await service.save_audio_feedback(mock_session, response_id, metrics)

            # Should be called with filler count 5 and word count 100
            mock_filler.assert_called_once_with(5, 100)

    @pytest.mark.asyncio
    async def test_calculates_overall_score_correctly(self):
        """Test that overall score is calculated with correct weights."""
        service = AudioService()
        response_id = uuid4()

        call_count = 0
        mock_response = MagicMock()
        mock_response.word_count = 100

        def mock_exec_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.first.return_value = None
            else:
                mock_result.first.return_value = mock_response
            return mock_result

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(side_effect=mock_exec_side_effect)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={},
            volume_consistency=80.0,  # 0.2 weight
            confidence_score=60.0,  # 0.2 weight
        )

        with (
            patch.object(service.analyzer, "calculate_speech_rate_score", return_value=100.0),
            patch.object(service.analyzer, "calculate_filler_score", return_value=90.0),
        ):
            await service.save_audio_feedback(mock_session, response_id, metrics)

        # Expected: 100*0.3 + 90*0.3 + 80*0.2 + 60*0.2 = 30 + 27 + 16 + 12 = 85
        # Check that the feedback was created with calculated score
        add_call = mock_session.add.call_args[0][0]
        expected_score = 100.0 * 0.3 + 90.0 * 0.3 + 80.0 * 0.2 + 60.0 * 0.2
        assert add_call.overall_audio_score == round(expected_score, 1)


class TestAudioMetricsHandling:
    """Tests for handling AudioMetrics data structures."""

    @pytest.mark.asyncio
    async def test_handles_empty_filler_words(self, tmp_path):
        """Test handling of empty filler words dict."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(text="Test", duration_seconds=60.0)
        mock_metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={},  # Empty
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service, "analyze_audio", new_callable=AsyncMock, return_value=mock_metrics
            ),
        ):
            transcript, metrics = await service.process_response_audio(
                mock_session, response_id, str(audio_file)
            )

        assert mock_response.filler_word_count == 0

    @pytest.mark.asyncio
    async def test_handles_multiple_filler_types(self, tmp_path):
        """Test handling of multiple filler word types."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(text="Test words here", duration_seconds=60.0)
        mock_metrics = AudioMetrics(
            speech_rate_wpm=130.0,
            filler_words={"um": 5, "uh": 3, "like": 10, "you know": 2},
            volume_consistency=85.0,
            confidence_score=75.0,
        )

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service, "analyze_audio", new_callable=AsyncMock, return_value=mock_metrics
            ),
        ):
            await service.process_response_audio(mock_session, response_id, str(audio_file))

        assert mock_response.filler_word_count == 20  # 5+3+10+2


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_handles_empty_transcript(self, tmp_path):
        """Test handling of empty transcript."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_response.word_count = None
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(text="", duration_seconds=5.0)
        mock_metrics = AudioMetrics(
            speech_rate_wpm=0.0,
            filler_words={},
            volume_consistency=50.0,
            confidence_score=50.0,
        )

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service, "analyze_audio", new_callable=AsyncMock, return_value=mock_metrics
            ),
        ):
            transcript, metrics = await service.process_response_audio(
                mock_session, response_id, str(audio_file)
            )

        # Empty transcript should result in word_count not being set (falsy check in code)
        assert transcript == ""

    @pytest.mark.asyncio
    async def test_handles_no_duration_in_transcription(self, tmp_path):
        """Test handling when transcription has no duration."""
        service = AudioService()
        response_id = uuid4()

        audio_file = tmp_path / "test.webm"
        audio_file.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_response.duration_seconds = 60  # Pre-existing duration
        mock_result = MagicMock()
        mock_result.first.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        mock_transcript = TranscriptionResult(text="Test", duration_seconds=None)
        mock_metrics = AudioMetrics(
            speech_rate_wpm=100.0,
            filler_words={},
            volume_consistency=80.0,
            confidence_score=70.0,
        )

        with (
            patch.object(
                service, "transcribe_audio", new_callable=AsyncMock, return_value=mock_transcript
            ),
            patch.object(
                service, "analyze_audio", new_callable=AsyncMock, return_value=mock_metrics
            ),
        ):
            await service.process_response_audio(mock_session, response_id, str(audio_file))

        # Duration should remain unchanged when transcription has no duration
        assert mock_response.duration_seconds == 60
