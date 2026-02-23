"""add refresh token fields to users

Revision ID: 0008_add_refresh_token
Revises: 0007_add_target_company
Create Date: 2025-12-04

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_add_refresh_token"
down_revision: str | None = "0007_add_target_company"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add refresh_token column
    op.add_column("users", sa.Column("refresh_token", sa.String(512), nullable=True))
    # Add refresh_token_expires_at column
    op.add_column(
        "users", sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "refresh_token_expires_at")
    op.drop_column("users", "refresh_token")
