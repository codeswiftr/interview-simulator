"""merge_video_and_comparison

Revision ID: cc9c049c241b
Revises: 0011_comparison_details, 0011_add_video_feedback
Create Date: 2025-12-12 06:11:10.895255+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'cc9c049c241b'
down_revision: Union[str, None] = ('0011_comparison_details', '0011_add_video_feedback')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
