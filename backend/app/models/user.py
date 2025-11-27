"""User model for Interview Simulator."""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class SubscriptionTier(str, Enum):
    """User subscription tiers."""

    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class User(SQLModel, table=True):
    """User account model."""

    __tablename__ = "users"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str | None = None

    # Subscription
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    subscription_status: str | None = Field(default=None)  # active, canceled, past_due, trialing, incomplete
    subscription_expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Stripe integration
    stripe_customer_id: str | None = Field(default=None, index=True)
    stripe_subscription_id: str | None = Field(default=None)

    # Usage tracking
    interviews_this_month: int = Field(default=0)
    total_interviews: int = Field(default=0)

    # Status
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=now_utc, sa_column=Column(DateTime(timezone=True))
    )
    last_login_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class UserCreate(SQLModel):
    """Schema for user creation."""

    email: str
    password: str
    full_name: str | None = None


class UserLogin(SQLModel):
    """Schema for user login."""

    email: str
    password: str


class UserRead(SQLModel):
    """Schema for user response."""

    id: UUID
    email: str
    full_name: str | None
    subscription_tier: SubscriptionTier
    interviews_this_month: int
    total_interviews: int
    created_at: datetime


class Token(SQLModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
