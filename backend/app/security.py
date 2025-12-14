"""Security utilities for password hashing and JWT handling."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256

from app.config import settings

# Configure password hashing context with migration support
# Primary: pbkdf2_sha256 (fallback)
# We'll handle bcrypt directly to avoid passlib compatibility issues
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

ALGORITHM = "HS256"
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hash prefixes for identification
BCRYPT_PREFIX = "$2b$"
PBKDF2_PREFIX = "$pbkdf2-sha256$"


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    All new passwords will be hashed with bcrypt for improved security.

    Note: bcrypt has a 72-byte limit, so longer passwords are truncated.
    This is a bcrypt limitation, not a security issue.
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')

    # Generate salt and hash with 12 rounds
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash.

    Supports both bcrypt and legacy pbkdf2_sha256 hashes for backward compatibility.
    Returns True if password is valid.
    """
    try:
        # Check if it's a bcrypt hash
        if hashed_password.startswith(BCRYPT_PREFIX):
            # Bcrypt verification
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        else:
            # Legacy pbkdf2_sha256 verification
            return pbkdf2_sha256.verify(plain_password, hashed_password)
    except Exception as e:
        # Log the error for security monitoring
        # In production, you might want to use a proper logger
        print(f"Password verification error: {e}")
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash needs to be rehashed.

    This is used for lazy migration - when a user with a legacy pbkdf2 hash
    successfully logs in, we should rehash their password with bcrypt.

    Returns:
        True if the password should be rehashed (i.e., it's using pbkdf2)
    """
    # If it's not a bcrypt hash, it needs rehashing
    return not hashed_password.startswith(BCRYPT_PREFIX)


def is_legacy_hash(hashed_password: str) -> bool:
    """Check if a password hash uses the legacy pbkdf2_sha256 algorithm.

    Args:
        hashed_password: The password hash to check

    Returns:
        True if the hash is pbkdf2_sha256, False if it's bcrypt
    """
    return hashed_password.startswith(PBKDF2_PREFIX)


def migrate_password_hash(plain_password: str) -> str:
    """Migrate a plaintext password to the current secure hashing algorithm.

    This should be called after successful password verification when
    needs_rehash() returns True.

    Args:
        plain_password: The user's plaintext password

    Returns:
        New bcrypt hash of the password
    """
    return hash_password(plain_password)


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
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
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


def verify_refresh_token(
    stored_token: str | None, provided_token: str, expires_at: datetime | None
) -> bool:
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
    return not datetime.now(UTC) > expires_at
