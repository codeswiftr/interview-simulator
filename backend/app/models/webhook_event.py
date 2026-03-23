"""SQLModel for idempotent Stripe webhook event processing."""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class ProcessedWebhookEvent(SQLModel, table=True):
    """Tracks processed Stripe webhook event IDs for idempotency.

    Prevents double-processing when Stripe retries events (e.g., due to
    non-2xx responses or network timeouts).
    """

    __tablename__ = "processed_webhook_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    stripe_event_id: str = Field(index=True, unique=True, max_length=255)
    event_type: str = Field(max_length=100)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    result: str = Field(default="success", max_length=255)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
