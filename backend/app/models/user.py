"""User model for Interview Simulator."""

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import EmailStr, StringConstraints
from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

# Constrained string types for input validation
StrictName = Annotated[str, StringConstraints(min_length=1, max_length=200, strip_whitespace=True)]
StrictEmail = EmailStr
StrictPassword = Annotated[str, StringConstraints(min_length=8, max_length=128)]
StrictToken = Annotated[str, StringConstraints(min_length=1, max_length=512)]


class SubscriptionTier(str, Enum):
    """User subscription tiers."""

    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class ExperienceLevel(str, Enum):
    """User experience level for personalized feedback."""

    JUNIOR = "junior"  # 0-2 years experience
    MID = "mid"  # 2-5 years experience
    SENIOR = "senior"  # 5+ years experience


class User(SQLModel, table=True):
    """User account model."""

    __tablename__ = "users"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str | None = None

    # Experience level for personalized feedback
    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.MID, sa_column=Column(String, nullable=False, default="mid")
    )

    # Subscription - use sa_column to force String type (avoid PostgreSQL enum)
    subscription_tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE, sa_column=Column(String, nullable=False, default="free")
    )
    subscription_status: str | None = Field(
        default=None
    )  # active, canceled, past_due, trialing, incomplete
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

    # Refresh Token
    refresh_token: str | None = Field(default=None, max_length=512)
    refresh_token_expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Timestamps
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
    last_login_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class UserCreate(SQLModel):
    """Schema for user creation with strict input validation."""

    email: StrictEmail
    password: StrictPassword
    full_name: StrictName | None = None
    experience_level: ExperienceLevel | None = None  # Optional during registration

    def model_post_init(self, __context: Any) -> None:
        """Validate password after model initialization."""
        from app.utils.password_validation import validate_password

        errors = validate_password(
            self.password,
            username=self.full_name if self.full_name else None,
            email=self.email
        )
        if errors:
            # Raise ValueError which FastAPI converts to 422 Unprocessable Entity
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")


class UserLogin(SQLModel):
    """Schema for user login with strict input validation."""

    email: StrictEmail
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class UserRead(SQLModel):
    """Schema for user response."""

    id: UUID
    email: str
    full_name: str | None
    experience_level: ExperienceLevel
    subscription_tier: SubscriptionTier
    interviews_this_month: int
    total_interviews: int
    created_at: datetime


class Token(SQLModel):
    """JWT token response with refresh token."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshTokenRequest(SQLModel):
    """Request schema for token refresh."""

    refresh_token: StrictToken


class UserUpdate(SQLModel):
    """Schema for updating user profile with strict validation."""

    full_name: StrictName | None = None
    email: StrictEmail | None = None
    experience_level: ExperienceLevel | None = None


class PasswordChange(SQLModel):
    """Schema for changing password with strict validation."""

    current_password: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    new_password: StrictPassword

    def model_post_init(self, __context: Any) -> None:
        """Validate new password after model initialization."""
        from app.utils.password_validation import validate_password

        errors = validate_password(self.new_password)
        if errors:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")
