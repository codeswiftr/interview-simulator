"""Audio transcription service using OpenAI Whisper API."""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result from transcription service."""

    text: str
    duration_seconds: float | None = None
    language: str | None = None
    segments: list[dict] | None = None


class Transcriber:
    """Transcribes audio files using OpenAI Whisper API.

    Supports:
    - Multiple audio formats (mp3, wav, webm, m4a, etc.)
    - Timestamped segments
    - Language detection
    """

    SUPPORTED_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    MAX_FILE_SIZE_MB = 25

    def __init__(self) -> None:
        """Initialize the transcriber."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe(
        self,
        audio_path: str | Path,
        language: str | None = None,
        include_timestamps: bool = False,
    ) -> TranscriptionResult:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'en', 'es')
            include_timestamps: Whether to include word-level timestamps

        Returns:
            TranscriptionResult with transcript and metadata

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If audio file doesn't exist
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Validate file format
        suffix = audio_path.suffix.lower().lstrip(".")
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Check file size
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large: {file_size_mb:.1f}MB. "
                f"Maximum size: {self.MAX_FILE_SIZE_MB}MB"
            )

        try:
            with open(audio_path, "rb") as audio_file:
                # Build transcription options
                options: dict = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json" if include_timestamps else "json",
                }

                if language:
                    options["language"] = language

                response = await self.client.audio.transcriptions.create(**options)

            # Parse response based on format
            if include_timestamps:
                segments = [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                    }
                    for seg in getattr(response, "segments", [])
                ]
                return TranscriptionResult(
                    text=response.text,
                    duration_seconds=getattr(response, "duration", None),
                    language=getattr(response, "language", None),
                    segments=segments if segments else None,
                )
            else:
                return TranscriptionResult(
                    text=response.text,
                    language=getattr(response, "language", None),
                )

        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise

    async def transcribe_bytes(
        self,
        audio_data: bytes,
        filename: str = "audio.webm",
        language: str | None = None,
        include_timestamps: bool = False,
    ) -> TranscriptionResult:
        """Transcribe audio from bytes.

        Args:
            audio_data: Raw audio bytes
            filename: Filename with extension for format detection
            language: Optional language code
            include_timestamps: Whether to include timestamps

        Returns:
            TranscriptionResult with transcript
        """
        # Write to temp file and transcribe
        suffix = Path(filename).suffix or ".webm"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_data)
            tmp.flush()
            return await self.transcribe(
                tmp.name,
                language=language,
                include_timestamps=include_timestamps,
            )

    def estimate_cost(self, duration_seconds: float) -> float:
        """Estimate transcription cost.

        Args:
            duration_seconds: Audio duration in seconds

        Returns:
            Estimated cost in USD (Whisper charges $0.006 per minute)
        """
        minutes = duration_seconds / 60
        return minutes * 0.006
