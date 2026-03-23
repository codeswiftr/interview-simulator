"""Add performance indexes for feedback tables

This migration adds explicit indexes on response_id columns for feedback tables
to improve query performance when looking up feedback by response.

NOTE: The AudioFeedback and ContentFeedback models already have unique=True on
response_id fields, which creates unique indexes. However, this migration explicitly
ensures these indexes exist with consistent naming for better maintainability.

For VideoFeedback, response_id also has unique=True creating an implicit index.

Revision ID: f0ba3e56c2e0
Revises: 0012_add_interview_shares
Create Date: 2026-02-01 12:32:24.156259+00:00

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f0ba3e56c2e0"
down_revision: str | None = "0012_add_interview_shares"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes for feedback tables.

    These indexes improve query performance when looking up feedback by response_id.
    Note: Unique constraints on response_id already create implicit indexes, but we
    create explicit indexes here for consistency and to ensure they exist even if
    the unique constraints are modified in the future.
    """
    # Create indexes on response_id columns for faster lookups
    # These tables already have unique constraints on response_id, but we add
    # explicit indexes for clarity and to ensure optimal query performance

    # Note: Using CREATE INDEX IF NOT EXISTS to avoid errors if the indexes
    # already exist from unique constraints
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audio_feedback_response_id ON audio_feedback (response_id)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_content_feedback_response_id "
        "ON content_feedback (response_id)"
    )

    # Also add for video_feedback for consistency
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_video_feedback_response_id ON video_feedback (response_id)"
    )


def downgrade() -> None:
    """Remove performance indexes for feedback tables.

    Note: We only drop the explicitly named indexes. The unique constraint
    indexes will remain intact.
    """
    # Drop the explicit indexes (unique constraint indexes remain)
    op.execute("DROP INDEX IF EXISTS idx_video_feedback_response_id")
    op.execute("DROP INDEX IF EXISTS idx_content_feedback_response_id")
    op.execute("DROP INDEX IF EXISTS idx_audio_feedback_response_id")
