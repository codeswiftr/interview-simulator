"""Add processing status to interview responses

Revision ID: 0003_processing_status
Revises: 0002_timezone
Create Date: 2025-01-27 12:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_processing_status"
down_revision = "0002_timezone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add processing_status column with default
    op.add_column(
        "interview_responses",
        sa.Column("processing_status", sa.String(), server_default="pending", nullable=False),
    )

    # Add processing_error column
    op.add_column(
        "interview_responses",
        sa.Column("processing_error", sa.String(), nullable=True),
    )


def downgrade() -> None:
    # Remove processing_error column
    op.drop_column("interview_responses", "processing_error")

    # Remove processing_status column
    op.drop_column("interview_responses", "processing_status")

