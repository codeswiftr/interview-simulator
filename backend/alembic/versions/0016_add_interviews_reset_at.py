"""add interviews_reset_at to user table

Revision ID: 0016
Revises: 0015
Create Date: 2026-02-22 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0016'
down_revision: Union[str, None] = '0015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('interviews_reset_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'interviews_reset_at')
