"""Add team organization models

This migration adds the Organization, OrganizationMember, and OrganizationInvitation
tables to support B2B team features. It also adds the team_id nullable foreign key
column to the users table.

Revision ID: b1c2d3e4f5a6
Revises: f0ba3e56c2e0
Create Date: 2026-03-19 00:00:00.000000+00:00

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "f0ba3e56c2e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create organization tables and add team_id to users.

    Tables created:
    - organizations: top-level org record with seat licensing
    - organization_members: join table linking users to orgs
    - organization_invitations: pending/accepted/expired invite tokens

    Column added:
    - users.team_id: nullable FK to organizations.id
    """

    # --- Create organizations table ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("subscription_status", sa.String(), nullable=True),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seat_count", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("seats_used", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organizations_owner_id ON organizations (owner_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organizations_stripe_customer_id "
        "ON organizations (stripe_customer_id)"
    )

    # --- Create organization_members table ---
    op.create_table(
        "organization_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invited_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_member"),
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organization_members_org_id ON organization_members (org_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organization_members_user_id "
        "ON organization_members (user_id)"
    )

    # --- Create organization_invitations table ---
    op.create_table(
        "organization_invitations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("invited_by", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="member"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_organization_invitations_token "
        "ON organization_invitations (token)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organization_invitations_org_id "
        "ON organization_invitations (org_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organization_invitations_email "
        "ON organization_invitations (email)"
    )

    # --- Add team_id to users (nullable — existing rows keep NULL) ---
    op.add_column(
        "users",
        sa.Column("team_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_team_id_organizations",
        "users",
        "organizations",
        ["team_id"],
        ["id"],
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_team_id ON users (team_id)"
    )


def downgrade() -> None:
    """Reverse: drop team_id from users and drop organization tables."""

    # Drop FK and index on users.team_id first
    op.execute("DROP INDEX IF EXISTS ix_users_team_id")
    op.drop_constraint("fk_users_team_id_organizations", "users", type_="foreignkey")
    op.drop_column("users", "team_id")

    # Drop invitations table
    op.execute("DROP INDEX IF EXISTS ix_organization_invitations_email")
    op.execute("DROP INDEX IF EXISTS ix_organization_invitations_org_id")
    op.execute("DROP INDEX IF EXISTS ix_organization_invitations_token")
    op.drop_table("organization_invitations")

    # Drop members table
    op.execute("DROP INDEX IF EXISTS ix_organization_members_user_id")
    op.execute("DROP INDEX IF EXISTS ix_organization_members_org_id")
    op.drop_table("organization_members")

    # Drop organizations table
    op.execute("DROP INDEX IF EXISTS ix_organizations_stripe_customer_id")
    op.execute("DROP INDEX IF EXISTS ix_organizations_owner_id")
    op.execute("DROP INDEX IF EXISTS ix_organizations_slug")
    op.drop_table("organizations")
