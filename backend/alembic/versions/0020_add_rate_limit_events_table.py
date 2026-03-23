"""Add rate_limit_events table for PostgreSQL-backed rate limiting.

Replaces Redis for rate limiting as part of Rails 8 Phase 1.1 — dropping
the Redis dependency from the Interview Simulator backend.

Revision ID: 0020_add_rate_limit_events_table
Revises: 0019_add_processed_webhook_events
Create Date: 2026-03-21 00:00:00.000000+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020_add_rate_limit_events_table"
down_revision: str = "0019_add_processed_webhook_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", "window_start", name="uq_rate_limit_key_window"),
    )
    op.create_index("ix_rate_limit_events_key", "rate_limit_events", ["key"])
    op.create_index(
        "ix_rate_limit_events_window_start", "rate_limit_events", ["window_start"]
    )


def downgrade() -> None:
    op.drop_index("ix_rate_limit_events_window_start", table_name="rate_limit_events")
    op.drop_index("ix_rate_limit_events_key", table_name="rate_limit_events")
    op.drop_table("rate_limit_events")
