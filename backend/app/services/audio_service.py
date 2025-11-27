"""Audio processing service that orchestrates transcription and analysis."""

import logging
from pathlib import Path
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.audio_analyzer import AudioAnalyzer, AudioMetrics
from app.ai.transcriber import TranscriptionResult, Transcriber
from app.models.feedback import AudioFeedback
from app.models.interview import InterviewResponse

logger = logging.getLogger(__name__)


class AudioService:
    """Orchestrates audio processing pipeline: transcription → audio analysis → storage.

    Handles:
    - Transcribing audio files using Whisper
    - Analyzing audio metrics using Librosa
    - Storing results in database
    """

    def __init__(self) -> None:
        """Initialize audio service with transcriber and analyzer."""
        self.transcriber = Transcriber()
        self.analyzer = AudioAnalyzer()

    async def process_response_audio(
        self,
        session: AsyncSession,
        response_id: UUID,
        audio_path: str,
    ) -> tuple[str, AudioMetrics]:
        """Process audio for an interview response.

        Main entry point that:
        1. Transcribes the audio file
        2. Analyzes audio metrics
        3. Updates the response record with transcript
        4. Returns transcript and metrics

        Args:
            session: Database session
            response_id: UUID of the interview response
            audio_path: Path to the audio file

        Returns:
            Tuple of (transcript_text, audio_metrics)

        Raises:
            ValueError: If response not found or processing fails
        """
        # Verify response exists
        result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = result.first()
        if not response:
            raise ValueError(f"Response {response_id} not found")

        # Verify audio file exists
        if not Path(audio_path).exists():
            raise ValueError(f"Audio file not found: {audio_path}")

        try:
            # Step 1: Transcribe audio
            logger.info(f"Transcribing audio for response {response_id}")
            transcript_result = await self.transcribe_audio(audio_path)
            transcript_text = transcript_result.text

            # Step 2: Update response with transcript
            response.transcript = transcript_text
            if transcript_result.duration_seconds:
                response.duration_seconds = int(transcript_result.duration_seconds)
            if transcript_text:
                response.word_count = len(transcript_text.split())
            await session.commit()

            # Step 3: Analyze audio
            logger.info(f"Analyzing audio for response {response_id}")
            metrics = await self.analyze_audio(audio_path, transcript_text)

            # Step 4: Calculate filler word count
            total_fillers = sum(metrics.filler_words.values())
            response.filler_word_count = total_fillers
            await session.commit()

            return transcript_text, metrics

        except Exception as e:
            logger.error(f"Audio processing failed for response {response_id}: {e}", exc_info=True)
            raise ValueError(f"Failed to process audio: {str(e)}") from e

    async def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            TranscriptionResult with transcript text and metadata

        Raises:
            ValueError: If transcription fails
        """
        try:
            result = await self.transcriber.transcribe(
                audio_path,
                include_timestamps=False,
            )
            return result
        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}", exc_info=True)
            raise ValueError(f"Transcription failed: {str(e)}") from e

    async def analyze_audio(self, audio_path: str, transcript: str | None) -> AudioMetrics:
        """Analyze audio file for speech patterns.

        Args:
            audio_path: Path to the audio file
            transcript: Optional transcript text

        Returns:
            AudioMetrics with analysis results

        Raises:
            ValueError: If analysis fails
        """
        try:
            metrics = await self.analyzer.analyze(audio_path, transcript)
            return metrics
        except Exception as e:
            logger.error(f"Audio analysis failed for {audio_path}: {e}", exc_info=True)
            raise ValueError(f"Audio analysis failed: {str(e)}") from e

    async def save_audio_feedback(
        self,
        session: AsyncSession,
        response_id: UUID,
        metrics: AudioMetrics,
    ) -> AudioFeedback:
        """Save audio feedback to database.

        Args:
            session: Database session
            response_id: UUID of the response
            metrics: AudioMetrics from analysis

        Returns:
            Created AudioFeedback record

        Raises:
            ValueError: If response not found or feedback already exists
        """
        # Check if feedback already exists
        existing = await session.exec(
            select(AudioFeedback).where(AudioFeedback.response_id == response_id)
        )
        if existing.first():
            raise ValueError(f"AudioFeedback already exists for response {response_id}")

        # Calculate scores
        speech_rate_score = self.analyzer.calculate_speech_rate_score(metrics.speech_rate_wpm)

        total_fillers = sum(metrics.filler_words.values())
        # Get word count from response if available
        response_result = await session.exec(
            select(InterviewResponse).where(InterviewResponse.id == response_id)
        )
        response = response_result.first()
        word_count = response.word_count if response and response.word_count else 100

        filler_score = self.analyzer.calculate_filler_score(total_fillers, word_count)

        # Calculate overall audio score (weighted average)
        overall_score = (
            speech_rate_score * 0.3
            + filler_score * 0.3
            + metrics.volume_consistency * 0.2
            + metrics.confidence_score * 0.2
        )

        # Create feedback record
        feedback = AudioFeedback(
            response_id=response_id,
            speech_rate_wpm=metrics.speech_rate_wpm,
            speech_rate_score=speech_rate_score,
            filler_words=metrics.filler_words,
            filler_word_score=filler_score,
            volume_consistency=metrics.volume_consistency,
            confidence_score=metrics.confidence_score,
            overall_audio_score=round(overall_score, 1),
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        return feedback

