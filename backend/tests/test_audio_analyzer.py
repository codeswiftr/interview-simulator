"""Tests for audio analyzer service."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.ai.audio_analyzer import AudioAnalyzer, AudioMetrics


@pytest.fixture
def audio_analyzer():
    """Create AudioAnalyzer instance."""
    return AudioAnalyzer()


@pytest.fixture
def mock_audio_file(tmp_path):
    """Create a mock audio file."""
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"fake audio data")
    return str(audio_file)


class TestAudioAnalyzer:
    """Test suite for AudioAnalyzer."""

    def test_detect_filler_words(self, audio_analyzer):
        """Test filler word detection in transcript."""
        transcript = "Um, I think that, uh, the solution is, like, basically correct."
        fillers = audio_analyzer._detect_filler_words(transcript)

        assert "um" in fillers
        assert "uh" in fillers
        assert "like" in fillers
        assert "basically" in fillers
        assert fillers["um"] == 1
        assert fillers["uh"] == 1

    def test_calculate_speech_rate_score_optimal_range(self, audio_analyzer):
        """Test that optimal WPM range scores 100."""
        # Test optimal range (120-150 WPM)
        assert audio_analyzer.calculate_speech_rate_score(120.0) == 100.0
        assert audio_analyzer.calculate_speech_rate_score(135.0) == 100.0
        assert audio_analyzer.calculate_speech_rate_score(150.0) == 100.0

        # Test below optimal
        assert audio_analyzer.calculate_speech_rate_score(100.0) < 100.0

        # Test above optimal
        assert audio_analyzer.calculate_speech_rate_score(200.0) < 100.0

    def test_calculate_filler_score_low_fillers(self, audio_analyzer):
        """Test that low filler ratio scores high."""
        # < 2% fillers = 100
        assert audio_analyzer.calculate_filler_score(1, 100) == 100.0
        assert audio_analyzer.calculate_filler_score(2, 100) == 100.0

        # > 10% fillers = 0
        assert audio_analyzer.calculate_filler_score(11, 100) == 0.0
        assert audio_analyzer.calculate_filler_score(20, 100) == 0.0

        # Between 2% and 10% = linear interpolation
        score = audio_analyzer.calculate_filler_score(5, 100)
        assert 0 < score < 100

    @pytest.mark.asyncio
    async def test_analyze_returns_real_speech_rate(
        self, audio_analyzer, mock_audio_file, tmp_path
    ):
        """Test that speech rate is calculated from audio duration."""
        transcript = "This is a test transcript with ten words total here"

        with patch("app.ai.audio_analyzer.librosa.load") as mock_load:
            # Mock audio: 10 words in 5 seconds = 120 WPM
            mock_y = np.array([0.1] * 22050 * 5)  # 5 seconds at 22050 Hz
            mock_sr = 22050
            mock_load.return_value = (mock_y, mock_sr)

            metrics = await audio_analyzer.analyze(mock_audio_file, transcript)

            assert metrics.speech_rate_wpm > 0
            # Should be close to 120 WPM (10 words / 5 seconds * 60)

    @pytest.mark.asyncio
    async def test_analyze_calculates_volume_consistency(
        self, audio_analyzer, mock_audio_file
    ):
        """Test that volume consistency is calculated."""
        with patch("app.ai.audio_analyzer.librosa.load") as mock_load, patch(
            "app.ai.audio_analyzer.librosa.feature.rms"
        ) as mock_rms:
            mock_y = np.array([0.1] * 22050)
            mock_sr = 22050
            mock_load.return_value = (mock_y, mock_sr)

            # Mock consistent volume (low variance)
            mock_rms.return_value = np.array([[0.5] * 100])

            metrics = await audio_analyzer.analyze(mock_audio_file, "Test transcript")

            assert 0 <= metrics.volume_consistency <= 100

    @pytest.mark.asyncio
    async def test_analyze_detects_filler_words(
        self, audio_analyzer, mock_audio_file
    ):
        """Test that filler words are detected in transcript."""
        transcript = "Um, I think that, uh, the solution is correct."

        with patch("app.ai.audio_analyzer.librosa.load") as mock_load:
            mock_y = np.array([0.1] * 22050)
            mock_sr = 22050
            mock_load.return_value = (mock_y, mock_sr)

            metrics = await audio_analyzer.analyze(mock_audio_file, transcript)

            assert "um" in metrics.filler_words
            assert "uh" in metrics.filler_words
            assert metrics.filler_words["um"] == 1
            assert metrics.filler_words["uh"] == 1

    @pytest.mark.asyncio
    async def test_analyze_handles_missing_transcript(
        self, audio_analyzer, mock_audio_file
    ):
        """Test that analysis works without transcript."""
        with patch("app.ai.audio_analyzer.librosa.load") as mock_load:
            mock_y = np.array([0.1] * 22050)
            mock_sr = 22050
            mock_load.return_value = (mock_y, mock_sr)

            metrics = await audio_analyzer.analyze(mock_audio_file, None)

            # Should use estimated WPM
            assert metrics.speech_rate_wpm > 0
            assert metrics.filler_words == {}

    @pytest.mark.asyncio
    async def test_analyze_handles_invalid_audio_file(self, audio_analyzer):
        """Test that invalid audio files raise ValueError."""
        with pytest.raises(ValueError, match="Audio file not found"):
            await audio_analyzer.analyze("/nonexistent/file.wav", "Test")

