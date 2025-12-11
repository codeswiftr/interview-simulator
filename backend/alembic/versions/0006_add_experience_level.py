"""add experience level to user

Revision ID: 0006_add_experience_level
Revises: 0005_password_reset_tokens
Create Date: 2025-12-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0006_add_experience_level'
down_revision: str | None = '0005_password_reset_tokens'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add experience_level column with default value 'mid'
    op.add_column(
        'users',
        sa.Column('experience_level', sa.String(), nullable=False, server_default='mid')
    )


def downgrade() -> None:
    op.drop_column('users', 'experience_level')
