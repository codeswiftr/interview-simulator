"""Interview session models."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.types import JSON, String
from sqlmodel import Field, SQLModel


class InterviewType(str, Enum):
    """Types of interview sessions."""

    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    SYSTEM_DESIGN = "system_design"
    MIXED = "mixed"


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class InterviewStatus(str, Enum):
    """Interview session status."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    CANCELLED = "cancelled"


class ProcessingStatus(str, Enum):
    """Response processing status."""

    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewSession(SQLModel, table=True):
    """Interview session model."""

    __tablename__ = "interview_sessions"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Configuration
    interview_type: InterviewType = Field(sa_column=Column(String))
    company_style: str | None = Field(
        default=None, description="e.g., 'faang', 'startup', 'enterprise'"
    )
    target_company: str | None = Field(
        default=None, description="Target company for interview prep (e.g., 'google', 'amazon')"
    )
    question_count: int = Field(default=5)
    difficulty: DifficultyLevel | None = Field(
        default=None, sa_column=Column(String), description="Preferred difficulty level"
    )

    # Status
    status: InterviewStatus = Field(
        default=InterviewStatus.SCHEDULED, sa_column=Column(String, default="scheduled")
    )

    # Timing
    scheduled_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ended_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    duration_seconds: int | None = None

    # Scores (populated after analysis)
    overall_score: float | None = None
    audio_score: float | None = None
    content_score: float | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class InterviewQuestion(SQLModel, table=True):
    """Link between interview session and questions."""

    __tablename__ = "interview_questions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="interview_sessions.id", index=True)
    question_id: UUID = Field(foreign_key="questions.id")

    order: int = Field(description="Order in the interview")
    asked_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    time_limit_seconds: int = Field(default=180)


class InterviewResponse(SQLModel, table=True):
    """User's response to an interview question."""

    __tablename__ = "interview_responses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="interview_sessions.id", index=True)
    question_id: UUID = Field(foreign_key="questions.id")

    # Media
    audio_url: str | None = None
    video_url: str | None = None

    # Transcription
    transcript: str | None = None
    transcript_with_timestamps: dict | None = Field(default=None, sa_column=Column(JSON))

    # Metrics
    duration_seconds: int = 0
    word_count: int | None = None
    filler_word_count: int | None = None

    # Processing status
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        sa_column=Column(String),
        description="Status of audio processing: transcribing, analyzing, completed, failed",
    )
    processing_error: str | None = Field(
        default=None, description="Error message if processing failed"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=InterviewSession.now_utc, sa_column=Column(DateTime(timezone=True))
    )


class InterviewSessionCreate(SQLModel):
    """Schema for creating interview session."""

    interview_type: InterviewType = InterviewType.BEHAVIORAL
    company_style: str | None = None
    target_company: str | None = None
    question_count: int = 5
    difficulty: DifficultyLevel | None = None
    scheduled_at: datetime | None = None


class InterviewSessionRead(SQLModel):
    """Schema for interview session response."""

    id: UUID
    interview_type: InterviewType
    company_style: str | None
    target_company: str | None
    status: InterviewStatus
    question_count: int
    overall_score: float | None
    duration_seconds: int | None
    created_at: datetime
    # Optional usage tracking fields (populated by endpoint)
    remaining_interviews: int | None = None


class InterviewResponseCreate(SQLModel):
    """Schema for creating an interview response."""

    question_id: UUID
    audio_url: str | None = None
    video_url: str | None = None
    transcript: str | None = None
    duration_seconds: int = 0


class QuestionInResponse(SQLModel):
    """Minimal question data embedded in response."""

    id: UUID
    content: str
    category: str
    difficulty: str


class InterviewResponseRead(SQLModel):
    """Schema for interview response output."""

    id: UUID
    session_id: UUID
    question_id: UUID
    audio_url: str | None
    video_url: str | None
    transcript: str | None
    duration_seconds: int
    word_count: int | None
    filler_word_count: int | None
    processing_status: ProcessingStatus
    processing_error: str | None
    created_at: datetime
    question: QuestionInResponse | None = None
