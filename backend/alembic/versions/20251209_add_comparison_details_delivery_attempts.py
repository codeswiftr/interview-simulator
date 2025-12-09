"""Add comparison_details to delivery_attempts."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251209_add_comparison_details_delivery_attempts"
down_revision = "085fbd9abb08_add_answer_preparation_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "delivery_attempts",
        sa.Column("comparison_details", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("delivery_attempts", "comparison_details")
