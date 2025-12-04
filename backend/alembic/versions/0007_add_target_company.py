"""add target_company to interview sessions

Revision ID: 0007_add_target_company
Revises: 0006_add_experience_level
Create Date: 2025-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_add_target_company'
down_revision: Union[str, None] = '0006_add_experience_level'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add target_company column (nullable for existing sessions)
    op.add_column(
        'interview_sessions',
        sa.Column('target_company', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('interview_sessions', 'target_company')
