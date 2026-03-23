"""Answer preparation models for AI Ghostwriter feature."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey
from sqlalchemy.types import String
from sqlmodel import Field, SQLModel


class PreparationStage(StrEnum):
    """Stages of answer preparation."""

    DETECTIVE = "detective"  # Gathering context via Q&A
    DRAFT = "draft"  # Draft generated, ready for review
    PRACTICE = "practice"  # User practicing delivery
    COMPLETE = "complete"  # Delivery rated, preparation complete


class AnswerPreparation(SQLModel, table=True):
    """Tracks answer preparation sessions for AI Ghostwriter feature."""

    __tablename__ = "answer_preparations"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    question_id: UUID = Field(foreign_key="questions.id", index=True)

    # Stage tracking
    stage: PreparationStage = Field(default=PreparationStage.DETECTIVE, sa_column=Column(String))

    # Generated content
    draft_answer: str | None = Field(default=None, description="AI-generated draft answer")

    # Timestamps
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class PreparationQnA(SQLModel, table=True):
    """Stores Q&A from detective stage of answer preparation."""

    __tablename__ = "preparation_qna"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    preparation_id: UUID = Field(
        sa_column=Column(
            ForeignKey("answer_preparations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )

    # Q&A content
    question: str = Field(description="Clarifying question asked by AI")
    answer: str = Field(description="User's answer to the question")
    order: int = Field(description="Order of question in the sequence")

    # Timestamps
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class DeliveryAttempt(SQLModel, table=True):
    """Tracks practice delivery attempts for prepared answers."""

    __tablename__ = "delivery_attempts"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    preparation_id: UUID = Field(
        sa_column=Column(
            ForeignKey("answer_preparations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )

    # Delivery content
    audio_url: str | None = Field(default=None, description="URL to recorded audio")
    transcript: str | None = Field(default=None, description="Transcribed delivery")

    # Rating
    delivery_score: float | None = Field(
        default=None, description="AI-generated delivery score (0-100)"
    )
    comparison_feedback: str | None = Field(
        default=None, description="AI feedback comparing delivery to draft"
    )
    comparison_details: dict | None = Field(
        default=None,
        description="Structured comparison data (strengths/improvements/etc.)",
        sa_column=Column(JSON, nullable=True),
    )

    # Timestamps
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
