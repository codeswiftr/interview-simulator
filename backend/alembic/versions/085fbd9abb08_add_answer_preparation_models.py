"""add_answer_preparation_models

Revision ID: 085fbd9abb08
Revises: 0008_add_refresh_token
Create Date: 2025-12-07 20:05:43.135951+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '085fbd9abb08'
down_revision: str | None = '0008_add_refresh_token'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create answer_preparations table
    op.create_table(
        "answer_preparations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("stage", sa.String(), nullable=False, server_default="detective"),
        sa.Column("draft_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_answer_preparations_user_id", "answer_preparations", ["user_id"])
    op.create_index("ix_answer_preparations_question_id", "answer_preparations", ["question_id"])

    # Create preparation_qna table
    op.create_table(
        "preparation_qna",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("preparation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answer_preparations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_preparation_qna_preparation_id", "preparation_qna", ["preparation_id"])

    # Create delivery_attempts table
    op.create_table(
        "delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("preparation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answer_preparations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("delivery_score", sa.Float(), nullable=True),
        sa.Column("comparison_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_delivery_attempts_preparation_id", "delivery_attempts", ["preparation_id"])


def downgrade() -> None:
    op.drop_table("delivery_attempts")
    op.drop_table("preparation_qna")
    op.drop_table("answer_preparations")
