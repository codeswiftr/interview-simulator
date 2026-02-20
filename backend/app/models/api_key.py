"""API Key model for Interview Simulator.

Provides secure API key management for programmatic access to the platform.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import StringConstraints
from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

# Constrained string types
StrictKeyName = Annotated[str, StringConstraints(min_length=1, max_length=100, strip_whitespace=True)]


class APIKeyScope(str, Enum):
    """Scopes for API key permissions."""

    READ = "read"  # Read-only access to user's data
    WRITE = "write"  # Create/modify user's data
    ADMIN = "admin"  # Full access (for admin keys)


class APIKey(SQLModel, table=True):
    """API Key model for programmatic access.

    API keys are stored hashed for security. The plain key is only shown once
    during creation and cannot be retrieved later.
    """

    __tablename__ = "api_keys"

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(UTC)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Human-readable name for the key
    name: str = Field(max_length=100, index=True)

    # Hashed key (bcrypt) - never store plain keys
    key_hash: str = Field(max_length=255)

    # Key prefix for identification (first 8 chars of the key)
    # Allows users to identify which key is being used without exposing full key
    key_prefix: str = Field(max_length=8, index=True)

    # Permissions
    scopes: str = Field(
        default="read", sa_column=Column(String, nullable=False, default="read")
    )  # Comma-separated scopes

    # Rate limiting metadata (requests per minute)
    rate_limit: int = Field(default=60)  # 60 requests per minute default
    last_used_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    request_count: int = Field(default=0)  # Total requests made with this key

    # Status
    is_active: bool = Field(default=True)
    expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Timestamps
    created_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=now_utc, sa_column=Column(DateTime(timezone=True)))

    def has_scope(self, scope: str) -> bool:
        """Check if this API key has the given scope.

        Args:
            scope: The scope to check (e.g., 'read', 'write', 'admin')

        Returns:
            True if the key has this scope or admin scope
        """
        key_scopes = [s.strip() for s in self.scopes.split(",")]
        return scope in key_scopes or "admin" in key_scopes

    def is_valid(self) -> bool:
        """Check if this API key is valid (active and not expired).

        Returns:
            True if the key can be used
        """
        if not self.is_active:
            return False

        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False

        return True


class APIKeyCreate(SQLModel):
    """Schema for creating a new API key."""

    name: StrictKeyName
    scopes: list[APIKeyScope] = [APIKeyScope.READ]
    rate_limit: int = Field(default=60, ge=1, le=1000)  # 1-1000 requests per minute
    expires_at: datetime | None = None


class APIKeyRead(SQLModel):
    """Schema for API key response (without the actual key)."""

    id: UUID
    user_id: UUID
    name: str
    key_prefix: str
    scopes: str
    rate_limit: int
    is_active: bool
    last_used_at: datetime | None
    request_count: int
    expires_at: datetime | None
    created_at: datetime


class APIKeyCreateResponse(SQLModel):
    """Response after creating an API key (includes the plain key once)."""

    key: str  # Plain key - only shown once
    api_key: APIKeyRead


class APIKeyUpdate(SQLModel):
    """Schema for updating an API key."""

    name: StrictKeyName | None = None
    scopes: list[APIKeyScope] | None = None
    rate_limit: int | None = Field(default=None, ge=1, le=1000)
    is_active: bool | None = None
    expires_at: datetime | None = None
