"""Login attempt tracking for account lockout functionality."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index
from sqlmodel import Field, SQLModel


class LoginAttempt(SQLModel, table=True):
    """Track failed login attempts for account lockout.

    After 5 failed attempts within 15 minutes, account is locked for 15 minutes.
    """

    __tablename__ = "login_attempts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True)
    ip_address: str
    success: bool = Field(default=False)
    attempted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Composite index for efficient lockout queries
    __table_args__ = (Index("idx_email_attempted_at", "email", "attempted_at"),)
