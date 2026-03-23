"""Background task service for async processing operations."""

import asyncio
import logging
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import SessionLocal
from app.models.interview import InterviewResponse, ProcessingStatus
from app.services.audio_service import AudioService
from app.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds


class BackgroundTaskService:
    """Manages background processing tasks for async operations.

    Handles:
    - Audio transcription and analysis
    - Content feedback generation
    - Session feedback generation
    """

    def __init__(self) -> None:
        """Initialize background task service."""
        self.audio_service = AudioService()
        self.feedback_service = FeedbackService()

    def _log_with_context(
        self,
        level: int,
        message: str,
        response_id: UUID | None = None,
        session_id: UUID | None = None,
        task_name: str | None = None,
        exc_info: bool = False,
        **kwargs,
    ) -> None:
        """Log message with correlation fields for background tasks.

        Args:
            level: Logging level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            response_id: Optional response ID for correlation
            session_id: Optional session ID for correlation
            task_name: Optional task name for correlation
            exc_info: Whether to include exception info in log
            **kwargs: Additional fields to include in log
        """
        extra = {}
        if response_id:
            extra["response_id"] = str(response_id)
        if session_id:
            extra["session_id"] = str(session_id)
        if task_name:
            extra["task_name"] = task_name

        extra.update(kwargs)
        logger.log(level, message, extra=extra, exc_info=exc_info)

    async def process_response_audio_async(
        self,
        response_id: UUID,
        audio_url: str,
    ) -> None:
        """Background task: Transcribes audio, analyzes it, updates response.

        This is a fire-and-forget task that processes audio in the background.
        Errors are logged but don't crash the application.

        Args:
            response_id: UUID of the interview response
            audio_url: URL path to the audio file
        """
        try:
            # Resolve audio URL to file path
            from pathlib import Path

            if not audio_url or not audio_url.startswith("/uploads/audio/"):
                logger.warning(f"Invalid audio URL for response {response_id}: {audio_url}")
                return

            relative_path = audio_url.lstrip("/")
            audio_path = Path(relative_path)
            if not audio_path.exists():
                audio_path = Path("backend") / relative_path

            if not audio_path.exists():
                logger.warning(f"Audio file not found: {audio_path} for response {response_id}")
                return

            # Create new session for background task
            async with SessionLocal() as session:
                try:
                    # Update status to TRANSCRIBING
                    result = await session.exec(
                        select(InterviewResponse).where(InterviewResponse.id == response_id)
                    )
                    response = result.first()
                    if response:
                        response.processing_status = ProcessingStatus.TRANSCRIBING
                        response.processing_error = None
                        await session.commit()

                    # Process audio with retry logic
                    transcript, metrics = await self._process_audio_with_retry(
                        session, response_id, str(audio_path)
                    )

                    # Update status to ANALYZING
                    if response:
                        response.processing_status = ProcessingStatus.ANALYZING
                        await session.commit()

                    # Save audio feedback
                    await self.audio_service.save_audio_feedback(session, response_id, metrics)

                    # Update status to COMPLETED
                    if response:
                        response.processing_status = ProcessingStatus.COMPLETED
                        await session.commit()

                    self._log_with_context(
                        logging.INFO,
                        f"Successfully processed audio for response {response_id}",
                        response_id=response_id,
                        session_id=response.session_id if response else None,
                        task_name="process_response_audio",
                        duration_seconds=response.duration_seconds if response else None,
                    )

                    # Auto-generate content feedback if transcript is available
                    await self.generate_content_feedback_async(response_id)

                except Exception as e:
                    self._log_with_context(
                        logging.ERROR,
                        f"Background audio processing failed for response {response_id}: {e}",
                        response_id=response_id,
                        task_name="process_response_audio",
                        exc_info=True,
                    )
                    # Update status to FAILED
                    await self._update_processing_status_failed(session, response_id, str(e))

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                f"Failed to start background audio processing for response {response_id}: {e}",
                response_id=response_id,
                task_name="process_response_audio",
                exc_info=True,
            )

    async def _process_audio_with_retry(
        self, session: AsyncSession, response_id: UUID, audio_path: str
    ) -> tuple[str, object]:
        """Process audio with retry logic for transient failures.

        Args:
            session: Database session
            response_id: UUID of the response
            audio_path: Path to audio file

        Returns:
            Tuple of (transcript, metrics)

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                transcript, metrics = await self.audio_service.process_response_audio(
                    session, response_id, audio_path
                )
                return transcript, metrics
            except (ValueError, ConnectionError, TimeoutError) as e:
                # Transient errors - retry
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    logger.warning(
                        f"Audio processing attempt {attempt + 1} failed for {response_id}, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Audio processing failed after {MAX_RETRIES} attempts for {response_id}: {e}"
                    )
            except Exception as e:
                # Permanent errors - don't retry
                logger.error(f"Permanent error in audio processing for {response_id}: {e}")
                raise

        # All retries exhausted
        raise last_error or Exception("Audio processing failed")

    async def _update_processing_status_failed(
        self, session: AsyncSession, response_id: UUID, error_message: str
    ) -> None:
        """Update response processing status to FAILED.

        Args:
            session: Database session
            response_id: UUID of the response
            error_message: Error message to store
        """
        try:
            result = await session.exec(
                select(InterviewResponse).where(InterviewResponse.id == response_id)
            )
            response = result.first()
            if response:
                response.processing_status = ProcessingStatus.FAILED
                response.processing_error = error_message[:500]  # Limit error message length
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to update processing status for {response_id}: {e}")

    async def generate_content_feedback_async(
        self,
        response_id: UUID,
    ) -> None:
        """Background task: Generates ContentFeedback for response if transcript exists.

        Args:
            response_id: UUID of the response to analyze
        """
        try:
            async with SessionLocal() as session:
                try:
                    # Check if feedback already exists
                    from sqlmodel import select

                    from app.models.feedback import ContentFeedback

                    existing = await session.exec(
                        select(ContentFeedback).where(ContentFeedback.response_id == response_id)
                    )
                    if existing.first():
                        self._log_with_context(
                            logging.DEBUG,
                            f"ContentFeedback already exists for response {response_id}",
                            response_id=response_id,
                            task_name="generate_content_feedback",
                        )
                        return

                    # Generate feedback
                    await self.feedback_service.generate_feedback(session, response_id)
                    self._log_with_context(
                        logging.INFO,
                        f"Successfully generated content feedback for response {response_id}",
                        response_id=response_id,
                        task_name="generate_content_feedback",
                    )

                    # Check if all responses now have feedback and auto-generate session feedback
                    await self._maybe_generate_session_feedback(session, response_id)

                except ValueError as e:
                    # Expected errors (e.g., no transcript, already exists)
                    self._log_with_context(
                        logging.DEBUG,
                        f"Could not generate feedback for response {response_id}: {e}",
                        response_id=response_id,
                        task_name="generate_content_feedback",
                    )
                except Exception as e:
                    self._log_with_context(
                        logging.ERROR,
                        f"Background content feedback generation failed for response {response_id}: {e}",
                        response_id=response_id,
                        task_name="generate_content_feedback",
                        exc_info=True,
                    )

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                f"Failed to start content feedback generation for response {response_id}: {e}",
                response_id=response_id,
                task_name="generate_content_feedback",
                exc_info=True,
            )

    async def _maybe_generate_session_feedback(
        self,
        session: AsyncSession,
        response_id: UUID,
    ) -> None:
        """Check if all responses have ContentFeedback and auto-generate SessionFeedback.

        This is called after each ContentFeedback is successfully generated to check
        if the session is now ready for aggregated feedback.

        Args:
            session: Database session
            response_id: UUID of the response that just got feedback
        """
        try:
            from app.models.feedback import ContentFeedback, SessionFeedback

            # Get the response to find its session
            response_result = await session.exec(
                select(InterviewResponse).where(InterviewResponse.id == response_id)
            )
            response = response_result.first()
            if not response:
                return

            session_id = response.session_id

            # Check if session feedback already exists
            existing_session_feedback = await session.exec(
                select(SessionFeedback).where(SessionFeedback.session_id == session_id)
            )
            if existing_session_feedback.first():
                self._log_with_context(
                    logging.DEBUG,
                    f"SessionFeedback already exists for session {session_id}",
                    session_id=session_id,
                    task_name="auto_session_feedback",
                )
                return

            # Get all responses for this session
            all_responses_result = await session.exec(
                select(InterviewResponse).where(InterviewResponse.session_id == session_id)
            )
            all_responses = list(all_responses_result.all())

            # Check if all responses have ContentFeedback
            all_have_feedback = True
            for resp in all_responses:
                feedback_result = await session.exec(
                    select(ContentFeedback).where(ContentFeedback.response_id == resp.id)
                )
                if not feedback_result.first():
                    all_have_feedback = False
                    break

            if not all_have_feedback:
                self._log_with_context(
                    logging.DEBUG,
                    f"Not all responses have feedback yet for session {session_id}",
                    session_id=session_id,
                    task_name="auto_session_feedback",
                )
                return

            # All responses have feedback - generate session feedback
            self._log_with_context(
                logging.INFO,
                f"All responses have feedback, generating session feedback for {session_id}",
                session_id=session_id,
                task_name="auto_session_feedback",
            )

            try:
                feedback = await self.feedback_service.generate_session_feedback(
                    session, session_id
                )
                self._log_with_context(
                    logging.INFO,
                    f"Successfully auto-generated session feedback for {session_id}",
                    session_id=session_id,
                    task_name="auto_session_feedback",
                    overall_score=feedback.overall_score if feedback else None,
                )
            except ValueError as e:
                self._log_with_context(
                    logging.WARNING,
                    f"Could not auto-generate session feedback for {session_id}: {e}",
                    session_id=session_id,
                    task_name="auto_session_feedback",
                )

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                f"Error checking for auto session feedback generation: {e}",
                response_id=response_id,
                task_name="auto_session_feedback",
                exc_info=True,
            )

    async def generate_session_feedback_async(
        self,
        session_id: UUID,
    ) -> None:
        """Background task: Generates SessionFeedback when interview ends.

        Waits a short delay to allow any in-flight response processing to complete,
        then generates aggregated session feedback.

        Args:
            session_id: UUID of the interview session
        """
        try:
            # Wait a bit for any in-flight response processing
            await asyncio.sleep(2)

            async with SessionLocal() as session:
                try:
                    # Check if feedback already exists
                    from sqlmodel import select

                    from app.models.feedback import SessionFeedback

                    existing = await session.exec(
                        select(SessionFeedback).where(SessionFeedback.session_id == session_id)
                    )
                    if existing.first():
                        self._log_with_context(
                            logging.DEBUG,
                            f"SessionFeedback already exists for session {session_id}",
                            session_id=session_id,
                            task_name="generate_session_feedback",
                        )
                        return

                    # Generate session feedback
                    feedback = await self.feedback_service.generate_session_feedback(
                        session, session_id
                    )
                    self._log_with_context(
                        logging.INFO,
                        f"Successfully generated session feedback for session {session_id}",
                        session_id=session_id,
                        task_name="generate_session_feedback",
                        overall_score=feedback.overall_score if feedback else None,
                    )

                except ValueError as e:
                    # Expected errors (e.g., no responses, already exists)
                    self._log_with_context(
                        logging.DEBUG,
                        f"Could not generate session feedback for {session_id}: {e}",
                        session_id=session_id,
                        task_name="generate_session_feedback",
                    )
                except Exception as e:
                    self._log_with_context(
                        logging.ERROR,
                        f"Background session feedback generation failed for session {session_id}: {e}",
                        session_id=session_id,
                        task_name="generate_session_feedback",
                        exc_info=True,
                    )

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                f"Failed to start session feedback generation for session {session_id}: {e}",
                session_id=session_id,
                task_name="generate_session_feedback",
                exc_info=True,
            )


# Global instance
background_tasks = BackgroundTaskService()
