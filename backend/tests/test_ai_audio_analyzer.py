"""Comprehensive tests for audio analysis using Librosa.

Tests cover:
- Speech rate calculation
- Filler word detection
- Volume consistency analysis
- Confidence scoring from pitch
- Edge cases and error handling
"""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.ai.audio_analyzer import AudioAnalyzer, AudioMetrics


class TestAudioAnalyzerInitialization:
    """Tests for audio analyzer initialization."""

    def test_analyzer_constants(self):
        """Test analyzer has expected constants defined."""
        analyzer = AudioAnalyzer()

        assert analyzer.FILLER_PATTERNS == [
            "um",
            "uh",
            "like",
            "you know",
            "basically",
            "actually",
            "so",
        ]
        assert analyzer.OPTIMAL_WPM_MIN == 120
        assert analyzer.OPTIMAL_WPM_MAX == 150


class TestFillerWordDetection:
    """Tests for filler word detection in transcripts."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    def test_detect_single_filler_words(self, analyzer: AudioAnalyzer):
        """Test detection of individual filler words."""
        transcript = "Um, I think that, uh, this is a good idea."

        fillers = analyzer._detect_filler_words(transcript)

        assert fillers == {"um": 1, "uh": 1}

    def test_detect_multiple_same_filler(self, analyzer: AudioAnalyzer):
        """Test counting multiple occurrences of same filler."""
        transcript = "Like, I was like, you know, like totally surprised."

        fillers = analyzer._detect_filler_words(transcript)

        assert fillers["like"] == 3
        assert fillers["you know"] == 1

    def test_detect_no_fillers(self, analyzer: AudioAnalyzer):
        """Test transcript with no filler words."""
        transcript = "This is a clean, professional response with no fillers."

        fillers = analyzer._detect_filler_words(transcript)

        assert fillers == {}

    def test_detect_case_insensitive(self, analyzer: AudioAnalyzer):
        """Test filler detection is case-insensitive."""
        transcript = "UM, LIKE, Uh, BASICALLY everything is broken."

        fillers = analyzer._detect_filler_words(transcript)

        assert fillers["um"] == 1
        assert fillers["like"] == 1
        assert fillers["uh"] == 1
        assert fillers["basically"] == 1

    def test_detect_phrase_fillers(self, analyzer: AudioAnalyzer):
        """Test detection of multi-word filler phrases."""
        transcript = "So, you know, I think you know that, you know, we should proceed."

        fillers = analyzer._detect_filler_words(transcript)

        assert fillers["you know"] == 3
        assert fillers["so"] == 1


class TestSpeechRateScoring:
    """Tests for speech rate scoring."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    def test_optimal_speech_rate_scores_100(self, analyzer: AudioAnalyzer):
        """Test optimal speech rate (120-150 WPM) scores 100."""
        assert analyzer.calculate_speech_rate_score(120) == 100.0
        assert analyzer.calculate_speech_rate_score(135) == 100.0
        assert analyzer.calculate_speech_rate_score(150) == 100.0

    def test_too_slow_speech_penalized(self, analyzer: AudioAnalyzer):
        """Test speech slower than optimal range is penalized."""
        score_110 = analyzer.calculate_speech_rate_score(110)  # 10 below min
        assert score_110 == 80.0  # 100 - (10 * 2)

        score_100 = analyzer.calculate_speech_rate_score(100)  # 20 below min
        assert score_100 == 60.0  # 100 - (20 * 2)

    def test_too_fast_speech_penalized(self, analyzer: AudioAnalyzer):
        """Test speech faster than optimal range is penalized."""
        score_160 = analyzer.calculate_speech_rate_score(160)  # 10 above max
        assert score_160 == 80.0  # 100 - (10 * 2)

        score_170 = analyzer.calculate_speech_rate_score(170)  # 20 above max
        assert score_170 == 60.0  # 100 - (20 * 2)

    def test_very_slow_speech_minimum_zero(self, analyzer: AudioAnalyzer):
        """Test very slow speech scores minimum of 0."""
        score = analyzer.calculate_speech_rate_score(50)  # 70 below min
        assert score == 0.0

    def test_very_fast_speech_minimum_zero(self, analyzer: AudioAnalyzer):
        """Test very fast speech scores minimum of 0."""
        score = analyzer.calculate_speech_rate_score(200)  # 50 above max
        assert score == 0.0


class TestFillerScoring:
    """Tests for filler word scoring."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    def test_no_fillers_scores_100(self, analyzer: AudioAnalyzer):
        """Test response with no fillers scores 100."""
        score = analyzer.calculate_filler_score(filler_count=0, word_count=100)
        assert score == 100.0

    def test_low_filler_ratio_scores_100(self, analyzer: AudioAnalyzer):
        """Test filler ratio < 2% scores 100."""
        # 1 filler in 100 words = 1% ratio
        score = analyzer.calculate_filler_score(filler_count=1, word_count=100)
        assert score == 100.0

        # 2 fillers in 100 words = 2% ratio (boundary)
        score = analyzer.calculate_filler_score(filler_count=2, word_count=100)
        assert score == 100.0

    def test_high_filler_ratio_scores_zero(self, analyzer: AudioAnalyzer):
        """Test filler ratio >= 10% scores 0."""
        # 10 fillers in 100 words = 10% ratio
        score = analyzer.calculate_filler_score(filler_count=10, word_count=100)
        assert score == 0.0

        # More than 10% also scores 0
        score = analyzer.calculate_filler_score(filler_count=15, word_count=100)
        assert score == 0.0

    def test_medium_filler_ratio_interpolated(self, analyzer: AudioAnalyzer):
        """Test filler ratios between 2-10% are linearly interpolated."""
        # 6% ratio = midpoint between 2% and 10%
        score = analyzer.calculate_filler_score(filler_count=6, word_count=100)
        assert score == pytest.approx(50.0, rel=0.1)

        # 4% ratio = closer to 2%
        score = analyzer.calculate_filler_score(filler_count=4, word_count=100)
        assert 50.0 < score < 100.0

    def test_zero_word_count_returns_100(self, analyzer: AudioAnalyzer):
        """Test zero word count edge case returns max score."""
        score = analyzer.calculate_filler_score(filler_count=5, word_count=0)
        assert score == 100.0


class TestSpeechRateCalculation:
    """Tests for internal speech rate calculation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    def test_calculate_speech_rate_with_transcript(self, analyzer: AudioAnalyzer):
        """Test WPM calculation from transcript and duration."""
        transcript = "This is a test sentence with exactly ten words here."
        duration = 60.0  # 1 minute

        wpm = analyzer._calculate_speech_rate("/path/audio.mp3", transcript, duration)

        assert wpm == 10.0  # 10 words / 1 minute

    def test_calculate_speech_rate_30_seconds(self, analyzer: AudioAnalyzer):
        """Test WPM calculation for 30-second audio."""
        transcript = " ".join(["word"] * 60)  # 60 words
        duration = 30.0  # 30 seconds

        wpm = analyzer._calculate_speech_rate("/path/audio.mp3", transcript, duration)

        assert wpm == 120.0  # (60 words / 30 seconds) * 60

    def test_calculate_speech_rate_no_transcript(self, analyzer: AudioAnalyzer):
        """Test fallback when no transcript provided.

        Should return estimated WPM (120.0).
        """
        wpm = analyzer._calculate_speech_rate("/path/audio.mp3", None, 60.0)

        assert wpm == 120.0

    def test_calculate_speech_rate_zero_duration(self, analyzer: AudioAnalyzer):
        """Test speech rate with zero duration.

        Should return 0.0 to avoid division by zero.
        """
        transcript = "Some words"
        wpm = analyzer._calculate_speech_rate("/path/audio.mp3", transcript, 0.0)

        assert wpm == 0.0


class TestVolumeConsistency:
    """Tests for volume consistency analysis."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    def test_consistent_volume_high_score(self, analyzer: AudioAnalyzer):
        """Test consistent volume gives high score.

        Create audio with very low variation in RMS energy.
        """
        # Simulate consistent audio (low std deviation)
        y = np.array([0.5] * 10000, dtype=np.float32)
        sr = 22050

        score = analyzer._analyze_volume_consistency(y, sr)

        assert score > 80.0

    def test_variable_volume_low_score(self, analyzer: AudioAnalyzer):
        """Test variable volume gives lower score.

        Create audio with high variation in RMS energy.
        """
        # Simulate variable audio (blocks of loud/quiet so RMS frames differ)
        y = np.concatenate(
            [
                np.full(2048, 0.05, dtype=np.float32),
                np.full(2048, 0.95, dtype=np.float32),
                np.full(2048, 0.05, dtype=np.float32),
                np.full(2048, 0.95, dtype=np.float32),
                np.full(2048, 0.05, dtype=np.float32),
            ]
        )
        sr = 22050

        score = analyzer._analyze_volume_consistency(y, sr)

        assert score < 60.0

    def test_empty_audio_default_score(self, analyzer: AudioAnalyzer):
        """Test empty audio returns default score."""
        y = np.array([], dtype=np.float32)
        sr = 22050

        score = analyzer._analyze_volume_consistency(y, sr)

        assert score == 50.0

    def test_silent_audio_default_score(self, analyzer: AudioAnalyzer):
        """Test silent audio (all zeros) returns default score."""
        y = np.zeros(10000, dtype=np.float32)
        sr = 22050

        score = analyzer._analyze_volume_consistency(y, sr)

        assert score == 50.0


class TestConfidenceScore:
    """Tests for confidence scoring based on pitch stability."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    @patch("app.ai.audio_analyzer._librosa.piptrack")
    @patch("app.ai.audio_analyzer._librosa.feature.rms")
    def test_stable_pitch_high_confidence(self, mock_rms, mock_piptrack, analyzer: AudioAnalyzer):
        """Test stable pitch gives high confidence score.

        Low variation in both pitch and volume = high confidence.
        """
        # Mock stable pitch — shape is (freq_bins, time_frames)
        mock_pitches = np.array([[200.0, 205.0, 198.0, 202.0]])
        mock_magnitudes = np.array([[1.0, 1.0, 1.0, 1.0]])
        mock_piptrack.return_value = (mock_pitches, mock_magnitudes)

        # Mock consistent volume
        mock_rms.return_value = np.array([[0.5, 0.5, 0.5, 0.5]])

        y = np.array([0.5] * 1000, dtype=np.float32)
        sr = 22050

        score = analyzer._calculate_confidence_score(y, sr)

        assert score > 70.0

    @patch("app.ai.audio_analyzer._librosa.piptrack")
    @patch("app.ai.audio_analyzer._librosa.feature.rms")
    def test_variable_pitch_low_confidence(self, mock_rms, mock_piptrack, analyzer: AudioAnalyzer):
        """Test variable pitch gives lower confidence score.

        High variation in pitch or volume = lower confidence.
        """
        # Mock highly variable pitch — shape is (freq_bins, time_frames)
        mock_pitches = np.array([[50.0, 400.0, 80.0, 350.0]])
        mock_magnitudes = np.array([[1.0, 1.0, 1.0, 1.0]])
        mock_piptrack.return_value = (mock_pitches, mock_magnitudes)

        # Mock highly variable volume
        mock_rms.return_value = np.array([[0.05, 0.95, 0.1, 0.9]])

        y = np.array([0.5] * 1000, dtype=np.float32)
        sr = 22050

        score = analyzer._calculate_confidence_score(y, sr)

        assert score < 70.0

    @patch("app.ai.audio_analyzer._librosa.piptrack")
    def test_no_pitch_detected_default_score(self, mock_piptrack, analyzer: AudioAnalyzer):
        """Test audio with no detectable pitch returns default score."""
        # Mock no valid pitches
        mock_pitches = np.array([[0.0], [0.0], [0.0]])
        mock_magnitudes = np.array([[0.0], [0.0], [0.0]])
        mock_piptrack.return_value = (mock_pitches, mock_magnitudes)

        y = np.array([0.01] * 1000, dtype=np.float32)
        sr = 22050

        score = analyzer._calculate_confidence_score(y, sr)

        assert score == 50.0

    @patch("app.ai.audio_analyzer._librosa.piptrack")
    def test_pitch_analysis_error_returns_default(self, mock_piptrack, analyzer: AudioAnalyzer):
        """Test error in pitch analysis returns default score."""
        mock_piptrack.side_effect = Exception("Pitch tracking failed")

        y = np.array([0.5] * 1000, dtype=np.float32)
        sr = 22050

        score = analyzer._calculate_confidence_score(y, sr)

        assert score == 50.0


class TestAnalyzeFullAudio:
    """Tests for the main analyze() method."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    @pytest.mark.asyncio
    @patch("app.ai.audio_analyzer._librosa.load")
    @patch("app.ai.audio_analyzer._librosa.piptrack")
    @patch("app.ai.audio_analyzer._librosa.feature.rms")
    async def test_analyze_success(
        self, mock_rms, mock_piptrack, mock_load, analyzer: AudioAnalyzer, tmp_path: Path
    ):
        """Test successful full audio analysis.

        Should return AudioMetrics with all fields populated.
        """
        # Create test audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"audio data")

        # Mock librosa
        y = np.array([0.5] * 22050, dtype=np.float32)
        sr = 22050
        mock_load.return_value = (y, sr)

        # Mock pitch tracking
        mock_pitches = np.array([[200.0], [200.0], [200.0]])
        mock_magnitudes = np.array([[1.0], [1.0], [1.0]])
        mock_piptrack.return_value = (mock_pitches, mock_magnitudes)

        # Mock RMS
        mock_rms.return_value = np.array([[0.5, 0.5, 0.5]])

        transcript = "This is a test response with exactly eight words."

        result = await analyzer.analyze(str(audio_file), transcript)

        assert isinstance(result, AudioMetrics)
        assert result.speech_rate_wpm > 0
        assert result.volume_consistency > 0
        assert result.confidence_score > 0
        assert isinstance(result.filler_words, dict)

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self, analyzer: AudioAnalyzer):
        """Test analyze with non-existent audio file.

        Should raise ValueError.
        """
        with pytest.raises(ValueError, match="Audio file not found"):
            await analyzer.analyze("/nonexistent/audio.mp3")

    @pytest.mark.asyncio
    @patch("app.ai.audio_analyzer._librosa.load")
    async def test_analyze_without_transcript(
        self, mock_load, analyzer: AudioAnalyzer, tmp_path: Path
    ):
        """Test analyze without providing transcript.

        Should still return metrics, but no filler word detection.
        """
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"audio data")

        y = np.array([0.5] * 22050, dtype=np.float32)
        sr = 22050
        mock_load.return_value = (y, sr)

        with (
            patch.object(analyzer, "_calculate_confidence_score", return_value=75.0),
            patch.object(analyzer, "_analyze_volume_consistency", return_value=80.0),
        ):
            result = await analyzer.analyze(str(audio_file), transcript=None)

            assert result.speech_rate_wpm == 120.0  # Default estimate
            assert result.filler_words == {}  # No transcript = no filler detection

    @pytest.mark.asyncio
    @patch("app.ai.audio_analyzer._librosa.load")
    async def test_analyze_with_fillers(self, mock_load, analyzer: AudioAnalyzer, tmp_path: Path):
        """Test analyze detects filler words when transcript provided."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"audio data")

        y = np.array([0.5] * 22050, dtype=np.float32)
        sr = 22050
        mock_load.return_value = (y, sr)

        transcript = "Um, I think, like, you know, this is a good idea."

        with (
            patch.object(analyzer, "_calculate_confidence_score", return_value=75.0),
            patch.object(analyzer, "_analyze_volume_consistency", return_value=80.0),
        ):
            result = await analyzer.analyze(str(audio_file), transcript)

            assert "um" in result.filler_words
            assert "like" in result.filler_words
            assert "you know" in result.filler_words

    @pytest.mark.asyncio
    @patch("app.ai.audio_analyzer._librosa.load")
    async def test_analyze_librosa_error(self, mock_load, analyzer: AudioAnalyzer, tmp_path: Path):
        """Test analyze handles Librosa errors gracefully.

        Should raise ValueError with helpful message.
        """
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"audio data")

        mock_load.side_effect = Exception("Corrupt audio file")

        with pytest.raises(ValueError, match="Failed to analyze audio"):
            await analyzer.analyze(str(audio_file))


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return AudioAnalyzer()

    @pytest.mark.asyncio
    @patch("app.ai.audio_analyzer._librosa.load")
    async def test_very_short_audio(self, mock_load, analyzer: AudioAnalyzer, tmp_path: Path):
        """Test analysis of very short audio (< 1 second).

        Should handle gracefully without errors.
        """
        audio_file = tmp_path / "short.mp3"
        audio_file.write_bytes(b"audio")

        # Mock 0.5 second audio
        y = np.array([0.5] * 11025, dtype=np.float32)
        sr = 22050
        mock_load.return_value = (y, sr)

        with (
            patch.object(analyzer, "_calculate_confidence_score", return_value=50.0),
            patch.object(analyzer, "_analyze_volume_consistency", return_value=50.0),
        ):
            result = await analyzer.analyze(str(audio_file))

            assert result is not None
            assert isinstance(result, AudioMetrics)

    def test_filler_detection_punctuation_handling(self, analyzer: AudioAnalyzer):
        """Test filler detection handles punctuation correctly."""
        transcript = "Um, like... you know? Uh, basically!"

        fillers = analyzer._detect_filler_words(transcript)

        # Should detect fillers regardless of punctuation
        assert fillers["um"] == 1
        assert fillers["like"] == 1
        assert fillers["you know"] == 1
        assert fillers["uh"] == 1
        assert fillers["basically"] == 1
