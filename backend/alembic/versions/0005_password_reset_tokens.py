"""Add password_reset_tokens table.

Revision ID: 0005_password_reset_tokens
Revises: 0004_add_difficulty
Create Date: 2025-12-02

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0005_password_reset_tokens"
down_revision = "0004_add_difficulty"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"])
    op.create_index(op.f("ix_password_reset_tokens_token"), "password_reset_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_password_reset_tokens_token"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_user_id"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
