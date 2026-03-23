"""Job handlers for forge-jobs DB-backed queue.

Each handler is an async callable that receives a payload dict and delegates
to the existing BackgroundTaskService methods. The service instance already
owns all retry logic, DB session management, and status transitions.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.services.background_tasks import background_tasks

logger = logging.getLogger(__name__)


async def handle_process_audio(payload: dict) -> None:
    """Process audio transcription for an interview response.

    Args:
        payload: Must contain ``response_id`` (str UUID) and ``audio_url`` (str).
    """
    response_id = UUID(payload["response_id"])
    audio_url: str = payload["audio_url"]
    logger.info("handle_process_audio: response_id=%s", response_id)
    await background_tasks.process_response_audio_async(response_id, audio_url)


async def handle_generate_feedback(payload: dict) -> None:
    """Generate AI content feedback for an interview response.

    Args:
        payload: Must contain ``response_id`` (str UUID).
    """
    response_id = UUID(payload["response_id"])
    logger.info("handle_generate_feedback: response_id=%s", response_id)
    await background_tasks.generate_content_feedback_async(response_id)


async def handle_generate_session_feedback(payload: dict) -> None:
    """Generate aggregated session feedback when an interview ends.

    Args:
        payload: Must contain ``session_id`` (str UUID).
    """
    session_id = UUID(payload["session_id"])
    logger.info("handle_generate_session_feedback: session_id=%s", session_id)
    await background_tasks.generate_session_feedback_async(session_id)
