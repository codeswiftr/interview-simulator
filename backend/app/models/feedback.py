"""Feedback models for interview analysis."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import JSON, String
from sqlmodel import Field, SQLModel


class AudioFeedback(SQLModel, table=True):
    """Audio analysis feedback for a response."""

    __tablename__ = "audio_feedback"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    response_id: UUID = Field(foreign_key="interview_responses.id", unique=True)

    # Speech metrics
    speech_rate_wpm: float = Field(description="Words per minute")
    speech_rate_score: float = Field(description="0-100, optimal: 120-150 WPM")

    # Filler words
    filler_words: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description='e.g., {"um": 5, "uh": 3}',
    )
    filler_word_score: float = Field(description="0-100, lower fillers = higher score")

    # Confidence indicators
    volume_consistency: float = Field(description="0-100")
    confidence_score: float = Field(description="0-100, based on pitch stability")

    # Overall
    overall_audio_score: float = Field(description="0-100 weighted average")

    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class ContentFeedback(SQLModel, table=True):
    """Content analysis feedback for a response."""

    __tablename__ = "content_feedback"

    now_utc = AudioFeedback.now_utc

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    response_id: UUID = Field(foreign_key="interview_responses.id", unique=True)

    # Content scores
    technical_accuracy: float = Field(description="0-100")
    star_adherence: float = Field(description="0-100, for behavioral questions")
    answer_structure: float = Field(description="0-100")
    completeness: float = Field(description="0-100")
    relevance: float = Field(description="0-100")

    # Overall
    overall_content_score: float = Field(description="0-100 weighted average")

    # Qualitative feedback
    strengths: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    improvements: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    detailed_feedback: str = Field(default="", description="Paragraph of feedback")

    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class SessionFeedback(SQLModel, table=True):
    """Aggregated feedback for entire interview session."""

    __tablename__ = "session_feedback"

    now_utc = AudioFeedback.now_utc

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="interview_sessions.id", unique=True)

    # Overall scores
    overall_score: float = Field(description="0-100")
    audio_score: float = Field(description="Average audio score across responses")
    content_score: float = Field(description="Average content score across responses")

    # Qualitative summary
    top_strengths: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    top_improvements: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    # Recommendations
    recommended_practice_areas: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String))
    )
    next_question_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Suggested questions for next session",
    )

    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class AudioFeedbackRead(SQLModel):
    """Schema for audio feedback response."""

    speech_rate_wpm: float
    speech_rate_score: float
    filler_words: dict
    filler_word_score: float
    confidence_score: float
    overall_audio_score: float


class ContentFeedbackRead(SQLModel):
    """Schema for content feedback response."""

    technical_accuracy: float
    answer_structure: float
    completeness: float
    overall_content_score: float
    strengths: list[str]
    improvements: list[str]
    detailed_feedback: str


class SessionFeedbackRead(SQLModel):
    """Schema for session feedback response."""

    overall_score: float
    audio_score: float
    content_score: float
    top_strengths: list[str]
    top_improvements: list[str]
    recommended_practice_areas: list[str]
