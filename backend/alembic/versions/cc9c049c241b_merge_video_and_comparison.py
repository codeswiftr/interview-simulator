"""merge_video_and_comparison

Revision ID: cc9c049c241b
Revises: 0011_comparison_details, 0011_add_video_feedback
Create Date: 2025-12-12 06:11:10.895255+00:00

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "cc9c049c241b"
down_revision: str | None = ("0011_comparison_details", "0011_add_video_feedback")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
