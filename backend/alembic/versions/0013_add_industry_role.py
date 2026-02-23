"""Add industry and role columns to questions.

Revision ID: 0013_add_industry_role
Revises: b9bf4a130d5b
Create Date: 2026-02-06

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0013_add_industry_role"
down_revision = "b9bf4a130d5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add industry column with default value and index
    op.add_column(
        "questions", sa.Column("industry", sa.String(), nullable=False, server_default="general")
    )
    op.create_index(op.f("ix_questions_industry"), "questions", ["industry"], unique=False)

    # Add role column with default value and index
    op.add_column(
        "questions", sa.Column("role", sa.String(), nullable=False, server_default="general")
    )
    op.create_index(op.f("ix_questions_role"), "questions", ["role"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_questions_role"), table_name="questions")
    op.drop_column("questions", "role")
    op.drop_index(op.f("ix_questions_industry"), table_name="questions")
    op.drop_column("questions", "industry")
