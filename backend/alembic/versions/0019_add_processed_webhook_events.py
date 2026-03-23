"""Add processed_webhook_events table for Stripe idempotency

Revision ID: 0019_add_processed_webhook_events
Revises: 0013_add_industry_role, 0018_add_activated_at, b1c2d3e4f5a6
Create Date: 2026-03-19 10:00:00.000000+00:00

Merges divergent heads and adds table for webhook event deduplication.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019_add_processed_webhook_events"
down_revision: tuple[str, ...] = (
    "0013_add_industry_role",
    "0018_add_activated_at",
    "b1c2d3e4f5a6",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processed_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("result", sa.String(length=255), nullable=False, server_default="success"),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_event_id"),
    )
    op.create_index(
        op.f("ix_processed_webhook_events_stripe_event_id"),
        "processed_webhook_events",
        ["stripe_event_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_processed_webhook_events_user_id"),
        "processed_webhook_events",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_processed_webhook_events_user_id"),
        table_name="processed_webhook_events",
    )
    op.drop_index(
        op.f("ix_processed_webhook_events_stripe_event_id"),
        table_name="processed_webhook_events",
    )
    op.drop_table("processed_webhook_events")
