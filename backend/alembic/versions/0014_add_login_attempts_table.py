"""Add login_attempts table for account lockout

Revision ID: 0014_add_login_attempts
Revises: f0ba3e56c2e0
Create Date: 2026-02-15 12:00:00.000000+00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0014_add_login_attempts"
down_revision: str | None = "f0ba3e56c2e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create login_attempts table for account lockout functionality."""
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on email for efficient lookups
    op.create_index(
        op.f("ix_login_attempts_email"),
        "login_attempts",
        ["email"],
        unique=False,
    )

    # Create composite index on email and attempted_at for lockout queries
    op.create_index(
        "idx_email_attempted_at",
        "login_attempts",
        ["email", "attempted_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove login_attempts table."""
    op.drop_index("idx_email_attempted_at", table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_email"), table_name="login_attempts")
    op.drop_table("login_attempts")
