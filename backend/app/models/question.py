"""Interview question models."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.types import String
from sqlmodel import Field, SQLModel


class QuestionCategory(str, Enum):
    """Question category types."""

    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    SYSTEM_DESIGN = "system_design"


class Difficulty(str, Enum):
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(SQLModel, table=True):
    """Interview question model."""

    __tablename__ = "questions"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content: str = Field(description="The question text")
    category: QuestionCategory = Field(sa_column=Column(String, index=True))
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM, sa_column=Column(String, index=True))

    # Tags for filtering
    company_tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Companies known to ask this question",
    )
    topic_tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Topic tags (e.g., 'arrays', 'leadership')",
    )

    # Guidance
    expected_duration_seconds: int = Field(default=180, description="Expected answer duration")
    sample_answer: str | None = Field(default=None, description="Example good answer")
    evaluation_criteria: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Criteria for evaluating answers",
    )

    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class QuestionCreate(SQLModel):
    """Schema for question creation."""

    content: str
    category: QuestionCategory
    difficulty: Difficulty
    company_tags: list[str] = []
    topic_tags: list[str] = []
    expected_duration_seconds: int = 180
    sample_answer: str | None = None
    evaluation_criteria: dict = {}


class QuestionRead(SQLModel):
    """Schema for question response."""

    id: UUID
    content: str
    category: QuestionCategory
    difficulty: Difficulty
    company_tags: list[str]
    topic_tags: list[str]
    expected_duration_seconds: int
