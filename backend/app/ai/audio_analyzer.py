"""Audio analysis service using Librosa for speech pattern analysis."""

from dataclasses import dataclass


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
        """
        # TODO: Implement actual audio analysis with Librosa
        # This is a placeholder implementation

        # For now, return mock data
        filler_words = {}
        if transcript:
            filler_words = self._detect_filler_words(transcript)

        return AudioMetrics(
            speech_rate_wpm=130.0,  # TODO: Calculate from audio
            filler_words=filler_words,
            volume_consistency=85.0,  # TODO: Calculate from audio
            confidence_score=75.0,  # TODO: Calculate from pitch analysis
        )

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
