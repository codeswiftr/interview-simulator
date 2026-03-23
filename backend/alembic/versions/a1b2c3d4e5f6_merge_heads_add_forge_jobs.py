"""merge heads and add forge_jobs table for DB-backed job queue

Merges the b9bf4a130d5b (analytics) and b1c2d3e4f5a6 (team org) divergent branches,
then creates the forge_jobs table for the DB-backed job queue (Rails 8 Phase 2.2).

Revision ID: a1b2c3d4e5f6
Revises: b9bf4a130d5b, b1c2d3e4f5a6
Create Date: 2026-03-21 00:00:00.000000+00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | tuple[str, ...] | None = ("b9bf4a130d5b", "b1c2d3e4f5a6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Merge divergent branches and create forge_jobs table."""
    op.create_table(
        "forge_jobs",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_forge_jobs_pending",
        "forge_jobs",
        ["job_type", "run_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    """Drop forge_jobs table."""
    op.drop_index("idx_forge_jobs_pending", table_name="forge_jobs")
    op.drop_table("forge_jobs")
