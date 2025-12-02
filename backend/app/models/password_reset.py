"""Password reset token model for Interview Simulator."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel


class PasswordResetToken(SQLModel, table=True):
    """Password reset token for secure password recovery."""

    __tablename__ = "password_reset_tokens"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)  # Generated with secrets.token_urlsafe(32)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    used: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
