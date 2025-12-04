"""Audio analysis service using Librosa for speech pattern analysis."""

import logging
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np

logger = logging.getLogger(__name__)


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
            # Load audio file
            y, sr = librosa.load(audio_path, sr=None)
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

    def _analyze_volume_consistency(self, y: np.ndarray, sr: int) -> float:
        """Analyze volume consistency using RMS energy.

        Args:
            y: Audio time series
            sr: Sample rate

        Returns:
            Score from 0-100, higher = more consistent volume
        """
        # Calculate RMS energy per frame
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        if len(rms) == 0 or np.std(rms) == 0:
            return 50.0  # Default score if no variation

        # Calculate coefficient of variation (std / mean)
        mean_rms = np.mean(rms)
        if mean_rms == 0:
            return 50.0

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
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

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

            # Also consider volume consistency
            rms = librosa.feature.rms(y=y)[0]
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
