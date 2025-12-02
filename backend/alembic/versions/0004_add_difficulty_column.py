"""Add difficulty column to interview_sessions.

Revision ID: 0004_add_difficulty
Revises: 0003_processing_status
Create Date: 2025-12-02

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_add_difficulty"
down_revision = "0003_processing_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column("difficulty", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("interview_sessions", "difficulty")
