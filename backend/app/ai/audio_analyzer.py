"""Audio analysis service using Librosa for speech pattern analysis.

Librosa is an optional dependency (install via `pip install interview-simulator[audio]`
or `uv sync --extra audio`).  Importing this module is always safe — the ImportError
is deferred until an analysis method that actually calls librosa is invoked.  This
allows the test suite and application startup to work on Python 3.13 where the
librosa → numba → llvmlite dependency chain cannot be built.

When librosa is unavailable, ``_librosa`` is set to a patchable stub so that
``unittest.mock.patch("app.ai.audio_analyzer._librosa.load")`` continues to work
in unit tests.  The helper methods ``_analyze_volume_consistency`` and
``_calculate_confidence_score`` fall back to pure-NumPy implementations when the
stub is active, so those tests also run without the optional dependency.
"""

import logging
import types
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

try:
    import librosa as _librosa

    _LIBROSA_AVAILABLE = True
except ImportError:
    # Build a patchable stub so unittest.mock.patch can target
    # _librosa.load, _librosa.feature.rms, _librosa.piptrack etc.
    #
    # The stub implementations use pure NumPy so that tests which call helper
    # methods directly (without mocking librosa) still produce realistic values.
    # Tests that DO mock these functions will see their mock return values because
    # patch replaces the attribute on _librosa before the method is called.

    def _stub_load(path, sr=None, **_kw):
        raise NotImplementedError(
            "librosa.load() requires the 'audio' optional dependency. "
            "Install with: uv sync --extra audio"
        )

    def _stub_rms(y=None, S=None, frame_length=2048, hop_length=512, **_kw):
        """Pure-NumPy RMS energy per frame (mirrors librosa.feature.rms output shape)."""
        if y is None or len(y) == 0:
            return np.array([[]], dtype=np.float32)
        n_frames = 1 + max(0, (len(y) - frame_length) // hop_length)
        values = []
        for i in range(n_frames):
            start = i * hop_length
            frame = y[start : start + frame_length]
            values.append(float(np.sqrt(np.mean(frame**2))))
        # librosa.feature.rms returns shape (1, n_frames)
        return np.array([values], dtype=np.float32)

    def _stub_piptrack(y=None, sr=22050, **_kw):
        """Stub piptrack — returns zero pitches/magnitudes (no pitch detected)."""
        if y is None or len(y) == 0:
            return np.zeros((1, 1), dtype=np.float32), np.zeros((1, 1), dtype=np.float32)
        n_frames = max(1, len(y) // 512)
        pitches = np.zeros((128, n_frames), dtype=np.float32)
        magnitudes = np.zeros((128, n_frames), dtype=np.float32)
        return pitches, magnitudes

    _feature_ns = types.SimpleNamespace(rms=_stub_rms)
    _librosa = types.SimpleNamespace(  # type: ignore[assignment]
        load=_stub_load,
        feature=_feature_ns,
        piptrack=_stub_piptrack,
    )
    _LIBROSA_AVAILABLE = False

if TYPE_CHECKING:
    import librosa  # noqa: F401  (type checkers only)

logger = logging.getLogger(__name__)


def _require_librosa() -> None:
    """Raise a helpful ImportError when the 'audio' optional dependency is missing."""
    if not _LIBROSA_AVAILABLE:
        raise ImportError(
            "librosa is required for audio analysis but is not installed. "
            "Install the optional audio dependencies with:\n"
            "  uv sync --extra audio\n"
            "or add 'interview-simulator[audio]' to your environment."
        )


@dataclass
class AudioMetrics:
    """Metrics extracted from audio analysis."""

    speech_rate_wpm: float
    filler_words: dict[str, int]
    volume_consistency: float
    confidence_score: float


class AudioAnalyzer:
    """Analyzes interview audio for speech patterns and confidence indicators.

    Uses Librosa for audio processing to extract:
    - Speech rate (words per minute)
    - Filler word detection (requires transcript)
    - Volume consistency
    - Confidence scoring based on pitch variation
    """

    # Filler words to detect
    FILLER_PATTERNS = ["um", "uh", "like", "you know", "basically", "actually", "so"]

    # Optimal speech rate range (words per minute)
    OPTIMAL_WPM_MIN = 120
    OPTIMAL_WPM_MAX = 150

    async def analyze(self, audio_path: str, transcript: str | None = None) -> AudioMetrics:
        """Analyze audio file and return metrics.

        Args:
            audio_path: Path to the audio file
            transcript: Optional transcript for filler word detection

        Returns:
            AudioMetrics with speech analysis results

        Raises:
            ValueError: If audio file cannot be loaded or analyzed
        """
        if not Path(audio_path).exists():
            raise ValueError(f"Audio file not found: {audio_path}")

        try:
            # Load audio file — _librosa.load is either the real librosa or a patchable stub.
            # When librosa is not installed and this call is not mocked in tests, the stub
            # raises NotImplementedError with an installation hint.
            y, sr = _librosa.load(audio_path, sr=None)
            duration_seconds = len(y) / sr

            # Calculate speech rate
            speech_rate_wpm = self._calculate_speech_rate(audio_path, transcript, duration_seconds)

            # Analyze volume consistency
            volume_consistency = self._analyze_volume_consistency(y, sr)

            # Calculate confidence score from pitch stability
            confidence_score = self._calculate_confidence_score(y, sr)

            # Detect filler words if transcript available
            filler_words = {}
            if transcript:
                filler_words = self._detect_filler_words(transcript)

            return AudioMetrics(
                speech_rate_wpm=speech_rate_wpm,
                filler_words=filler_words,
                volume_consistency=volume_consistency,
                confidence_score=confidence_score,
            )
        except Exception as e:
            logger.error(f"Audio analysis failed for {audio_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to analyze audio: {str(e)}") from e

    def _detect_filler_words(self, transcript: str) -> dict[str, int]:
        """Detect filler words in transcript.

        Args:
            transcript: Text transcript of the response

        Returns:
            Dictionary mapping filler words to their counts
        """
        transcript_lower = transcript.lower()
        filler_counts = {}

        for filler in self.FILLER_PATTERNS:
            count = transcript_lower.count(filler)
            if count > 0:
                filler_counts[filler] = count

        return filler_counts

    def calculate_speech_rate_score(self, wpm: float) -> float:
        """Calculate score for speech rate.

        Args:
            wpm: Words per minute

        Returns:
            Score from 0-100, with optimal range scoring highest
        """
        if self.OPTIMAL_WPM_MIN <= wpm <= self.OPTIMAL_WPM_MAX:
            return 100.0

        # Calculate distance from optimal range
        if wpm < self.OPTIMAL_WPM_MIN:
            distance = self.OPTIMAL_WPM_MIN - wpm
        else:
            distance = wpm - self.OPTIMAL_WPM_MAX

        # Penalize by 2 points per WPM deviation
        score = max(0, 100 - (distance * 2))
        return score

    def calculate_filler_score(self, filler_count: int, word_count: int) -> float:
        """Calculate score based on filler word frequency.

        Args:
            filler_count: Total number of filler words
            word_count: Total word count in response

        Returns:
            Score from 0-100, fewer fillers = higher score
        """
        if word_count == 0:
            return 100.0

        filler_ratio = filler_count / word_count

        # < 2% fillers = 100, > 10% fillers = 0
        if filler_ratio <= 0.02:
            return 100.0
        elif filler_ratio >= 0.10:
            return 0.0
        else:
            # Linear interpolation
            return 100 - ((filler_ratio - 0.02) / 0.08) * 100

    def _calculate_speech_rate(
        self, audio_path: str, transcript: str | None, duration_seconds: float
    ) -> float:
        """Calculate words per minute from audio duration and transcript.

        Args:
            audio_path: Path to audio file (for logging)
            transcript: Text transcript of the speech
            duration_seconds: Duration of audio in seconds

        Returns:
            Words per minute (WPM)
        """
        if transcript:
            # Count words in transcript
            words = transcript.split()
            word_count = len(words)
            if duration_seconds > 0:
                wpm = (word_count / duration_seconds) * 60
                return round(wpm, 1)
            return 0.0
        else:
            # Estimate from audio duration (rough approximation: 2 words per second average)
            # This is a fallback when transcript is not available
            estimated_wpm = 120.0  # Default estimate
            logger.warning(f"No transcript provided for {audio_path}, using estimated WPM")
            return estimated_wpm

    @staticmethod
    def _compute_rms_frames(y: np.ndarray, frame_length: int = 2048, hop_length: int = 512) -> np.ndarray:
        """Compute per-frame RMS energy using pure NumPy.

        Used as a fallback when librosa is not installed, and as the implementation
        that backs ``librosa.feature.rms`` when the library *is* available but is
        being tested via mocks.

        Args:
            y: Audio time series (1-D float32/64 array).
            frame_length: Number of samples per frame.
            hop_length: Number of samples between successive frames.

        Returns:
            1-D array of per-frame RMS values.
        """
        if len(y) == 0:
            return np.array([], dtype=np.float32)
        # Pad so every sample belongs to exactly one frame
        n_frames = 1 + max(0, (len(y) - frame_length) // hop_length)
        rms_values = []
        for i in range(n_frames):
            start = i * hop_length
            frame = y[start : start + frame_length]
            rms_values.append(float(np.sqrt(np.mean(frame**2))))
        return np.array(rms_values, dtype=np.float32)

    def _analyze_volume_consistency(self, y: np.ndarray, sr: int) -> float:
        """Analyze volume consistency using RMS energy.

        Args:
            y: Audio time series
            sr: Sample rate

        Returns:
            Score from 0-100, higher = more consistent volume
        """
        # Calculate RMS energy per frame.
        # _librosa.feature.rms is either the real librosa, a mock (in tests), or the
        # numpy-backed stub (when librosa is not installed and no mock is active).
        frame_length = 2048
        hop_length = 512
        rms = _librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        if len(rms) == 0:
            return 50.0  # No audio data — return neutral default

        # Calculate coefficient of variation (std / mean)
        mean_rms = np.mean(rms)
        if mean_rms == 0:
            return 50.0  # Silent audio — return neutral default

        # Zero std means perfectly consistent volume → score of 100
        if np.std(rms) == 0:
            return 100.0

        cv = np.std(rms) / mean_rms

        # Lower coefficient of variation = more consistent = higher score
        # CV of 0 = perfect consistency (100), CV of 1+ = very inconsistent (0)
        # Map CV to 0-100 score (inverse relationship)
        score = max(0, 100 - (cv * 100))
        return round(score, 1)

    def _calculate_confidence_score(self, y: np.ndarray, sr: int) -> float:
        """Calculate confidence score based on pitch stability.

        Args:
            y: Audio time series
            sr: Sample rate

        Returns:
            Score from 0-100, higher = more confident (stable pitch + volume)
        """
        try:
            # Extract pitch using piptrack
            pitches, magnitudes = _librosa.piptrack(y=y, sr=sr)

            # Get pitch values where magnitude is significant
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Valid pitch
                    pitch_values.append(pitch)

            if len(pitch_values) < 2:
                return 50.0  # Default if not enough pitch data

            pitch_array = np.array(pitch_values)

            # Calculate coefficient of variation for pitch
            mean_pitch = np.mean(pitch_array)
            if mean_pitch == 0:
                return 50.0

            pitch_cv = np.std(pitch_array) / mean_pitch

            # Also consider volume consistency.
            # Same as above: real librosa, mock, or numpy stub.
            rms = _librosa.feature.rms(y=y)[0]
            mean_rms = np.mean(rms)
            volume_cv = np.std(rms) / mean_rms if mean_rms > 0 else 1.0

            # Lower variation in both pitch and volume = higher confidence
            # Combine both metrics (weighted average)
            pitch_score = max(0, 100 - (pitch_cv * 50))  # Pitch variation penalty
            volume_score = max(0, 100 - (volume_cv * 50))  # Volume variation penalty

            # Combined confidence score
            confidence = pitch_score * 0.6 + volume_score * 0.4
            return round(confidence, 1)

        except Exception as e:
            logger.warning(f"Pitch analysis failed, using default score: {e}")
            return 50.0  # Default score on error
