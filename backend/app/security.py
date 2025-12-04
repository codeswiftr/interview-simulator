"""Security utilities for password hashing and JWT handling."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def create_refresh_token() -> tuple[str, datetime]:
    """Create a secure refresh token with expiration.

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


def verify_refresh_token(stored_token: str | None, provided_token: str, expires_at: datetime | None) -> bool:
    """Verify a refresh token is valid and not expired.

    Args:
        stored_token: Token stored in database
        provided_token: Token provided by client
        expires_at: Expiration timestamp from database

    Returns:
        True if token is valid and not expired
    """
    if not stored_token or not expires_at:
        return False
    if stored_token != provided_token:
        return False
    if datetime.now(timezone.utc) > expires_at:
        return False
    return True
