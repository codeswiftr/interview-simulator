"""Add video_feedback table for video analysis results."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_add_video_feedback"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create video_feedback table."""
    op.create_table(
        "video_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "response_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_responses.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("nervousness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("eye_contact_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("looking_away_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fidget_count", sa.Integer(), nullable=True),
        sa.Column("hand_gesture_frequency", sa.Float(), nullable=True),
        sa.Column("processing_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frame_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop video_feedback table."""
    op.drop_table("video_feedback")
