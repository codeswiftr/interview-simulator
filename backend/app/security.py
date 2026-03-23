"""Security utilities for password hashing and JWT handling.

Migrated to forge-auth (ForgeAuth) for JWT (S152 Week 2).
Password hashing remains local for backward compatibility.
"""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from forge_shared.auth.forge_auth import AuthError, ForgeAuth
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

REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hash prefixes for identification
BCRYPT_PREFIX = "$2b$"
PBKDF2_PREFIX = "$pbkdf2-sha256$"

# Initialize forge-auth instance (lazy singleton)
_forge_auth_instance: ForgeAuth | None = None


def get_forge_auth_instance() -> ForgeAuth:
    """Get or create the global ForgeAuth instance.

    Uses the ForgeAuth facade from forge-shared which wraps JWTAuth
    with a product-aware, tier-aware API.
    """
    global _forge_auth_instance
    if _forge_auth_instance is None:
        _forge_auth_instance = ForgeAuth(
            secret_key=settings.secret_key,
            algorithm="HS256",
            access_token_expire_minutes=settings.access_token_expire_minutes,
            refresh_token_expire_days=REFRESH_TOKEN_EXPIRE_DAYS,
            issuer="interview-simulator",
            audience="codeswiftr.com",
        )
    return _forge_auth_instance


# Keep backward-compatible alias used by dependencies.py
def get_jwt_auth_instance() -> ForgeAuth:
    """Backward-compatible alias for get_forge_auth_instance().

    Returns the global ForgeAuth instance (which exposes the same
    decode_token / create_access_token / create_refresh_token surface
    that the old JWTAuth did, plus the new ForgeAuth extras).
    """
    return get_forge_auth_instance()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    All new passwords will be hashed with bcrypt for improved security.

    Note: bcrypt has a 72-byte limit, so longer passwords are truncated.
    This is a bcrypt limitation, not a security issue.
    """
    # Convert password to bytes and truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")[:72]

    # Generate salt and hash with 12 rounds
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash.

    Supports both bcrypt and legacy pbkdf2_sha256 hashes for backward compatibility.
    Returns True if password is valid.
    """
    try:
        # Check if it's a bcrypt hash
        if hashed_password.startswith(BCRYPT_PREFIX):
            # Bcrypt verification (truncate to 72 bytes to match hashing)
            password_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        else:
            # Legacy pbkdf2_sha256 verification
            return pbkdf2_sha256.verify(plain_password, hashed_password)
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning("Password verification error: %s", e)
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


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token using SHA-256 for secure database storage.

    Refresh tokens should never be stored in plaintext. This function
    produces a hex-encoded SHA-256 digest that is safe to store and
    compare without revealing the original token value.

    Args:
        token: The raw JWT refresh token string.

    Returns:
        Hex-encoded SHA-256 hash of the token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    """Create a signed JWT access token using forge-auth.

    Maintains backward compatibility with the previous API.
    Expects data to have 'sub' (user_id) key.
    """
    auth = get_forge_auth_instance()
    user_id = data.get("sub")
    if not user_id:
        raise ValueError("Token data must include 'sub' (user_id)")

    # Extra claims are everything that isn't sub or email
    extra = {k: v for k, v in data.items() if k not in ["sub", "email"]}
    email = str(data.get("email", ""))

    return auth.create_access_token(
        user_id=str(user_id),
        products=["interview-simulator"],
        tier="free",  # interview-simulator manages its own subscription_tier
        email=email,
        extra=extra if extra else None,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token using forge-auth.

    Maintains backward compatibility with the previous API.
    Returns the payload as a dict or None if invalid.
    """
    try:
        auth = get_forge_auth_instance()
        payload = auth.decode_token(token)
        return {
            "sub": payload.sub,
            "email": payload.email,
            "exp": payload.exp,
            "iat": payload.iat,
        }
    except (AuthError, Exception):
        return None


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a JWT refresh token using forge-auth.

    Args:
        user_id: The user's ID to embed in the token.

    Returns:
        Tuple of (jwt_token_string, expiration_datetime)
    """
    auth = get_forge_auth_instance()
    token = auth.create_refresh_token(user_id=user_id)
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


def verify_refresh_token(
    stored_token_hash: str | None, provided_token: str, expires_at: datetime | None
) -> bool:
    """Verify a refresh token is valid, not expired, and has valid JWT signature.

    The database stores a SHA-256 hash of the refresh token (not the raw token).
    This function hashes the provided token and compares it against the stored hash.

    Args:
        stored_token_hash: SHA-256 hash of the token stored in database
        provided_token: Raw token string provided by the client
        expires_at: Expiration timestamp from database

    Returns:
        True if token hash matches, is not expired, and JWT signature is valid
    """
    if not stored_token_hash or not expires_at:
        return False
    # Compare the hash of the provided token against the stored hash
    if stored_token_hash != hash_refresh_token(provided_token):
        return False
    if datetime.now(UTC) > expires_at:
        return False
    # Verify JWT structure and signature
    try:
        auth = get_forge_auth_instance()
        payload = auth.decode_token(provided_token)
        return payload.type == "refresh"
    except (AuthError, Exception):
        return False
