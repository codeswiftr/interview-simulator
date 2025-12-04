"""add refresh token fields to users

Revision ID: 0008_add_refresh_token
Revises: 0007_add_target_company
Create Date: 2025-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008_add_refresh_token'
down_revision: Union[str, None] = '0007_add_target_company'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add refresh_token column
    op.add_column(
        'users',
        sa.Column('refresh_token', sa.String(512), nullable=True)
    )
    # Add refresh_token_expires_at column
    op.add_column(
        'users',
        sa.Column('refresh_token_expires_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'refresh_token_expires_at')
    op.drop_column('users', 'refresh_token')
