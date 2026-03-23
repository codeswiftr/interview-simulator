"""Add activated_at to users table.

Revision ID: 0018_add_activated_at
Revises: 0017_add_refresh_token_index
Create Date: 2026-03-10

"""

from alembic import op
import sqlalchemy as sa

revision = "0018_add_activated_at"
down_revision: str | None = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "activated_at")
