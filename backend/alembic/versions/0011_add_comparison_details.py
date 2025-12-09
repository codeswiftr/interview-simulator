"""Add comparison_details to delivery_attempts."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0011_comparison_details"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "delivery_attempts",
        sa.Column("comparison_details", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("delivery_attempts", "comparison_details")
