"""add index on user.refresh_token for fast token lookup

Revision ID: 0017
Revises: 0016
Create Date: 2026-02-23 22:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_user_refresh_token", "user", ["refresh_token"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_refresh_token", table_name="user")
