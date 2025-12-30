"""Interview sharing models for public share links."""

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


def generate_share_token() -> str:
    """Generate a secure, URL-safe share token."""
    return token_urlsafe(32)


def default_expiry() -> datetime:
    """Default expiry is 7 days from now."""
    return datetime.now(UTC) + timedelta(days=7)


class InterviewShare(SQLModel, table=True):
    """Share link for an interview session.

    Allows read-only access to interview results via public URL.
    """

    __tablename__ = "interview_shares"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    interview_id: UUID = Field(foreign_key="interview_sessions.id", index=True)
    token: str = Field(
        default_factory=generate_share_token,
        unique=True,
        index=True,
        description="Unique share token for URL",
    )
    created_by: UUID = Field(foreign_key="users.id", description="User who created the share")

    # Expiration
    expires_at: datetime = Field(
        default_factory=default_expiry,
        sa_column=Column(DateTime(timezone=True)),
        description="Share link expiration (default: 7 days)",
    )

    # Analytics
    view_count: int = Field(default=0, description="Number of times the share was viewed")

    # Timestamps
    created_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(DateTime(timezone=True)),
    )

    @property
    def is_expired(self) -> bool:
        """Check if share link has expired."""
        return datetime.now(UTC) > self.expires_at


class InterviewShareCreate(SQLModel):
    """Schema for creating a share link."""

    interview_id: UUID


class InterviewShareRead(SQLModel):
    """Schema for share link response."""

    id: UUID
    interview_id: UUID
    token: str
    expires_at: datetime
    view_count: int
    created_at: datetime
    share_url: str | None = None


class SharedInterviewRead(SQLModel):
    """Schema for viewing a shared interview (public)."""

    interview_type: str
    overall_score: float | None
    audio_score: float | None
    content_score: float | None
    question_count: int
    created_at: datetime
    shared_by: str  # First name or email prefix
    responses: list[dict] = []
