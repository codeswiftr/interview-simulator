"""add_interview_analytics_table

Revision ID: b9bf4a130d5b
Revises: f0ba3e56c2e0
Create Date: 2026-02-06 20:14:46.006147+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9bf4a130d5b"
down_revision: str | None = "f0ba3e56c2e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_analytics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("filler_word_count", sa.Integer(), nullable=False),
        sa.Column("filler_words_per_minute", sa.Float(), nullable=False),
        sa.Column("speaking_pace_wpm", sa.Float(), nullable=False),
        sa.Column("total_duration_seconds", sa.Float(), nullable=False),
        sa.Column("pause_count", sa.Integer(), nullable=False),
        sa.Column("avg_pause_duration", sa.Float(), nullable=False),
        sa.Column("star_compliance_score", sa.Float(), nullable=False),
        sa.Column("overall_confidence_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interview_analytics_session_id"),
        "interview_analytics",
        ["session_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_interview_analytics_user_id"), "interview_analytics", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_analytics_user_id"), table_name="interview_analytics")
    op.drop_index(op.f("ix_interview_analytics_session_id"), table_name="interview_analytics")
    op.drop_table("interview_analytics")
