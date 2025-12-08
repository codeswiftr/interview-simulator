"""Email verification token model for email change verification."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


class EmailVerificationToken(SQLModel, table=True):
    """Email verification token for email changes."""

    __tablename__ = "email_verification_tokens"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    new_email: str = Field(description="New email address to verify")
    token: str = Field(unique=True, index=True, description="Verification token")
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    used: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
