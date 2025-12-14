"""User model for Interview Simulator."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel


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
    """Schema for user creation."""

    email: str
    password: str
    full_name: str | None = None
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
            from pydantic import ValidationError
            raise ValidationError.from_exception_data(
                "UserCreate",
                [{"type": "value_error", "loc": ("password",), "msg": "\n".join(errors)}]
            )


class UserLogin(SQLModel):
    """Schema for user login."""

    email: str
    password: str


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

    refresh_token: str


class UserUpdate(SQLModel):
    """Schema for updating user profile."""

    full_name: str | None = None
    email: str | None = None
    experience_level: ExperienceLevel | None = None


class PasswordChange(SQLModel):
    """Schema for changing password."""

    current_password: str
    new_password: str

    def model_post_init(self, __context: Any) -> None:
        """Validate new password after model initialization."""
        from app.utils.password_validation import validate_password

        errors = validate_password(self.new_password)
        if errors:
            from pydantic import ValidationError
            raise ValidationError.from_exception_data(
                "PasswordChange",
                [{"type": "value_error", "loc": ("new_password",), "msg": "\n".join(errors)}]
            )
