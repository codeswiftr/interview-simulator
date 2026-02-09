"""Behavioral analytics models for interview analysis."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class InterviewAnalytics(SQLModel, table=True):
    """Behavioral analytics for interview sessions.

    Tracks speech patterns, filler words, pacing, and STAR method compliance
    to provide users with detailed behavioral insights and progress tracking.
    """

    __tablename__ = "interview_analytics"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    session_id: UUID = Field(foreign_key="interview_sessions.id", unique=True, index=True)

    # Filler word metrics
    filler_word_count: int = Field(default=0, description="Total filler words detected")
    filler_words_per_minute: float = Field(
        default=0.0, description="Filler words normalized by duration"
    )

    # Speaking pace
    speaking_pace_wpm: float = Field(default=0.0, description="Words per minute (WPM)")
    total_duration_seconds: float = Field(default=0.0, description="Total speaking duration")

    # Pause metrics
    pause_count: int = Field(default=0, description="Number of significant pauses detected")
    avg_pause_duration: float = Field(
        default=0.0, description="Average pause duration in seconds"
    )

    # STAR method compliance (0-100)
    star_compliance_score: float = Field(
        default=0.0,
        description="STAR method adherence score (0-100)",
        ge=0,
        le=100,
    )

    # Overall confidence (0-100)
    overall_confidence_score: float = Field(
        default=0.0,
        description="Overall confidence score based on delivery metrics (0-100)",
        ge=0,
        le=100,
    )

    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))


class InterviewAnalyticsRead(SQLModel):
    """Schema for analytics response."""

    id: UUID
    user_id: UUID
    session_id: UUID
    filler_word_count: int
    filler_words_per_minute: float
    speaking_pace_wpm: float
    total_duration_seconds: float
    pause_count: int
    avg_pause_duration: float
    star_compliance_score: float
    overall_confidence_score: float
    created_at: datetime


class ProgressDataPoint(SQLModel):
    """Single data point in progress over time."""

    session_id: UUID
    created_at: datetime
    filler_words_per_minute: float
    speaking_pace_wpm: float
    star_compliance_score: float
    overall_confidence_score: float


class ProgressResponse(SQLModel):
    """Progress over time response with multiple sessions."""

    data_points: list[ProgressDataPoint]
    total_sessions: int


class AnalyticsSummary(SQLModel):
    """Aggregated analytics summary for a user."""

    avg_filler_words_per_minute: float
    avg_speaking_pace_wpm: float
    avg_star_compliance_score: float
    avg_confidence_score: float
    total_sessions_analyzed: int
    improvement_filler_words: float | None = Field(
        default=None, description="Percentage improvement in filler words (negative = improvement)"
    )
    improvement_star_compliance: float | None = Field(
        default=None, description="Percentage improvement in STAR compliance"
    )
    improvement_confidence: float | None = Field(
        default=None, description="Percentage improvement in confidence"
    )
