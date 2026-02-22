"""API Key service for secure key generation and management."""

import secrets
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import bcrypt
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.api_key import APIKey, APIKeyCreate, APIKeyScope, APIKeyUpdate
from app.models.user import User


def generate_api_key() -> str:
    """Generate a cryptographically secure API key.

    Format: is_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (43 chars total)
    - Prefix 'is_' identifies it as an Interview Simulator key
    - 40 random URL-safe characters (no underscores for clean copy-paste)

    Returns:
        A secure API key string
    """
    # Use URL-safe base64 encoding (no padding) for clean keys
    # 30 bytes = 40 base64 characters, replace underscores with dashes
    random_part = secrets.token_urlsafe(30).replace("_", "-")
    return f"is_{random_part}"


def hash_api_key(key: str) -> str:
    """Hash an API key using bcrypt.

    Args:
        key: The plain API key to hash

    Returns:
        Bcrypt hash of the key
    """
    key_bytes = key.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(key_bytes, salt)
    return hashed.decode("utf-8")


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash.

    Args:
        plain_key: The plain API key to verify
        hashed_key: The stored bcrypt hash

    Returns:
        True if the key is valid
    """
    try:
        key_bytes = plain_key.encode("utf-8")
        hash_bytes = hashed_key.encode("utf-8")
        return bcrypt.checkpw(key_bytes, hash_bytes)
    except Exception:
        return False


async def create_api_key(
    session: AsyncSession, user_id: UUID, key_data: APIKeyCreate
) -> tuple[str, APIKey]:
    """Create a new API key for a user.

    Args:
        session: Database session
        user_id: ID of the user creating the key
        key_data: API key creation data

    Returns:
        Tuple of (plain_key, api_key_model)

    Raises:
        ValueError: If user not found or key limit exceeded
    """
    # Verify user exists
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if not user:
        raise ValueError("User not found")

    # Check user's existing key count (limit to 10 keys per user)
    existing_keys = await session.exec(
        select(APIKey).where(APIKey.user_id == user_id, APIKey.is_active == True)
    )
    if len(list(existing_keys.all())) >= 10:
        raise ValueError("Maximum number of API keys (10) reached. Delete unused keys first.")

    # Generate the API key
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)
    key_prefix = plain_key[:8]  # Store prefix for identification

    # Convert scopes list to comma-separated string
    scopes_str = ",".join([scope.value for scope in key_data.scopes])

    # Create the API key model
    api_key = APIKey(
        user_id=user_id,
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=scopes_str,
        rate_limit=key_data.rate_limit,
        expires_at=key_data.expires_at,
    )

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return plain_key, api_key


async def get_user_api_keys(session: AsyncSession, user_id: UUID) -> list[APIKey]:
    """Get all API keys for a user.

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        List of API keys (sorted by creation date, newest first)
    """
    result = await session.exec(
        select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())  # type: ignore
    )
    return list(result.all())


async def get_api_key_by_id(session: AsyncSession, key_id: UUID, user_id: UUID) -> APIKey | None:
    """Get a specific API key by ID (user must own the key).

    Args:
        session: Database session
        key_id: ID of the API key
        user_id: ID of the user (for ownership verification)

    Returns:
        API key if found and owned by user, None otherwise
    """
    result = await session.exec(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user_id)
    )
    return result.first()


async def update_api_key(
    session: AsyncSession, key_id: UUID, user_id: UUID, update_data: APIKeyUpdate
) -> APIKey | None:
    """Update an API key.

    Args:
        session: Database session
        key_id: ID of the API key to update
        user_id: ID of the user (for ownership verification)
        update_data: Update data

    Returns:
        Updated API key if found and owned by user, None otherwise
    """
    api_key = await get_api_key_by_id(session, key_id, user_id)
    if not api_key:
        return None

    # Update fields
    if update_data.name is not None:
        api_key.name = update_data.name
    if update_data.scopes is not None:
        api_key.scopes = ",".join([scope.value for scope in update_data.scopes])
    if update_data.rate_limit is not None:
        api_key.rate_limit = update_data.rate_limit
    if update_data.is_active is not None:
        api_key.is_active = update_data.is_active
    if update_data.expires_at is not None:
        api_key.expires_at = update_data.expires_at

    api_key.updated_at = datetime.now(UTC)

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return api_key


async def delete_api_key(session: AsyncSession, key_id: UUID, user_id: UUID) -> bool:
    """Delete an API key.

    Args:
        session: Database session
        key_id: ID of the API key to delete
        user_id: ID of the user (for ownership verification)

    Returns:
        True if deleted, False if not found or not owned by user
    """
    api_key = await get_api_key_by_id(session, key_id, user_id)
    if not api_key:
        return False

    await session.delete(api_key)
    await session.commit()

    return True


async def verify_api_key_and_get_user(session: AsyncSession, plain_key: str) -> User | None:
    """Verify an API key and return the associated user.

    Args:
        session: Database session
        plain_key: The plain API key to verify

    Returns:
        User if key is valid, None otherwise
    """
    if not plain_key.startswith("is_"):
        return None

    key_prefix = plain_key[:8]

    # Find all keys with this prefix (should be very few)
    result = await session.exec(
        select(APIKey).where(
            APIKey.key_prefix == key_prefix,
            APIKey.is_active == True,
        )
    )

    # Check each key with matching prefix
    for api_key in result.all():
        if verify_api_key(plain_key, api_key.key_hash):
            # Key is valid - check if expired
            if not api_key.is_valid():
                return None

            # Update last used timestamp
            api_key.last_used_at = datetime.now(UTC)
            api_key.request_count += 1
            session.add(api_key)
            await session.commit()

            # Fetch and return the user
            user_result = await session.exec(select(User).where(User.id == api_key.user_id))
            return user_result.first()

    return None


async def record_api_key_usage(session: AsyncSession, api_key: APIKey) -> None:
    """Record API key usage (called by middleware).

    Args:
        session: Database session
        api_key: The API key to update
    """
    api_key.last_used_at = datetime.now(UTC)
    api_key.request_count += 1
    session.add(api_key)
    await session.commit()
