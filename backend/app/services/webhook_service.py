"""Webhook event deduplication service for Stripe webhook idempotency.

Prevents double-processing of Stripe webhook retries by recording processed
event IDs in the database. Uses a context manager pattern for clean handling
of both success and failure paths.
"""

import logging
from types import TracebackType
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.webhook_event import ProcessedWebhookEvent

logger = logging.getLogger(__name__)


class DuplicateEventError(Exception):
    """Raised when a webhook event has already been processed."""


async def is_event_processed(db: AsyncSession, stripe_event_id: str) -> bool:
    """Check if a Stripe event has already been processed.

    Args:
        db: Active async database session.
        stripe_event_id: Stripe event ID to check.

    Returns:
        True if the event has already been processed, False otherwise.
    """
    result = await db.exec(
        select(ProcessedWebhookEvent).where(
            ProcessedWebhookEvent.stripe_event_id == stripe_event_id
        )
    )
    return result.first() is not None


async def mark_event_processed(
    db: AsyncSession,
    stripe_event_id: str,
    event_type: str,
    result: str = "success",
    user_id: Optional[UUID] = None,
) -> ProcessedWebhookEvent:
    """Record a Stripe event as processed.

    Args:
        db: Active async database session.
        stripe_event_id: Stripe event ID to record.
        event_type: Stripe event type (e.g., 'checkout.session.completed').
        result: Processing result description.
        user_id: Optional user ID associated with the event.

    Returns:
        The created ProcessedWebhookEvent record.

    Raises:
        DuplicateEventError: If the event was already processed (race condition).
    """
    record = ProcessedWebhookEvent(
        stripe_event_id=stripe_event_id,
        event_type=event_type,
        result=result,
        user_id=user_id,
    )
    db.add(record)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise DuplicateEventError(
            f"Event {stripe_event_id} already processed (race condition)"
        ) from e
    return record


class WebhookProcessor:
    """Async context manager for idempotent webhook event processing.

    Marks events as processed on entry (to claim them) and updates the
    result on exit. Raises DuplicateEventError if the event was already claimed.

    Usage:
        async with WebhookProcessor(db, stripe_event_id, event_type) as processor:
            # ... process event ...
            processor.set_result("success_description", user_id=user.id)
    """

    def __init__(self, db: AsyncSession, stripe_event_id: str, event_type: str) -> None:
        self._db = db
        self._stripe_event_id = stripe_event_id
        self._event_type = event_type
        self._result = "success"
        self._user_id: Optional[UUID] = None
        self._record: Optional[ProcessedWebhookEvent] = None

    def set_result(self, result: str, user_id: Optional[UUID] = None) -> None:
        """Set the processing result and optional associated user."""
        self._result = result
        self._user_id = user_id

    async def __aenter__(self) -> "WebhookProcessor":
        # Claim the event immediately to prevent concurrent processing
        self._record = await mark_event_processed(
            db=self._db,
            stripe_event_id=self._stripe_event_id,
            event_type=self._event_type,
            result="processing",
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self._record is None:
            return False

        if exc_type is DuplicateEventError:
            # Already processed by another worker — treat as success
            logger.info(f"Event {self._stripe_event_id} already claimed by another worker")
            return True  # Suppress the exception

        if exc_type is not None:
            # Processing failed — update record with error info
            self._record.result = f"error: {exc_type.__name__}"
            self._db.add(self._record)
            return False  # Let the exception propagate

        # Success — update with final result
        self._record.result = self._result
        if self._user_id is not None:
            self._record.user_id = self._user_id
        self._db.add(self._record)
        return False
