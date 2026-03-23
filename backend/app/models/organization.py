"""Organization and team membership models."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class MemberRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=200)
    slug: str = Field(unique=True, index=True, max_length=100)
    owner_id: UUID = Field(sa_column=Column(ForeignKey("users.id"), nullable=False, index=True))
    stripe_customer_id: str | None = Field(default=None, index=True)
    stripe_subscription_id: str | None = Field(default=None)
    subscription_status: str | None = Field(default=None)
    subscription_expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    seat_count: int = Field(default=5)
    seats_used: int = Field(default=1)
    created_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
    is_active: bool = Field(default=True)


class OrganizationRead(SQLModel):
    id: UUID
    name: str
    slug: str
    owner_id: UUID
    subscription_status: str | None
    seat_count: int
    seats_used: int
    is_active: bool
    created_at: datetime


class OrganizationMember(SQLModel, table=True):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_member"),)

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(
        sa_column=Column(
            ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    user_id: UUID = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    role: MemberRole = Field(default=MemberRole.MEMBER, sa_column=Column(String))
    joined_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
    invited_by: UUID | None = Field(default=None)


class OrganizationMemberRead(SQLModel):
    id: UUID
    org_id: UUID
    user_id: UUID
    role: MemberRole
    joined_at: datetime


class OrganizationInvitation(SQLModel, table=True):
    __tablename__ = "organization_invitations"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(
        sa_column=Column(
            ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    email: str = Field(index=True)
    invited_by: UUID = Field(
        sa_column=Column(ForeignKey("users.id"), nullable=False)
    )
    token: str = Field(unique=True, index=True)
    role: MemberRole = Field(default=MemberRole.MEMBER, sa_column=Column(String))
    status: InvitationStatus = Field(
        default=InvitationStatus.PENDING, sa_column=Column(String)
    )
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    accepted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )


class InvitationRead(SQLModel):
    id: UUID
    org_id: UUID
    email: str
    role: MemberRole
    status: InvitationStatus
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime
