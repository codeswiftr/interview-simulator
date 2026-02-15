"""Security utilities for password hashing and JWT handling.

Migrated to forge-shared auth for JWT (2026-02).
Password hashing remains local for backward compatibility.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from forge_shared.auth.jwt import JWTAuth, JWTConfig
from forge_shared.auth.models import Permission, PlanTier, UserRole
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

# Initialize forge-shared JWT auth
_jwt_auth_instance: JWTAuth | None = None


def get_jwt_auth_instance() -> JWTAuth:
    """Get or create the global JWT auth instance.

    This is used by the app to initialize forge-shared auth on startup.
    """
    global _jwt_auth_instance
    if _jwt_auth_instance is None:
        config = JWTConfig(
            secret_key=settings.secret_key,
            algorithm="HS256",
            access_token_expire_minutes=settings.access_token_expire_minutes,
            refresh_token_expire_days=REFRESH_TOKEN_EXPIRE_DAYS,
            issuer="interview-simulator",
            audience="codeswiftr.com",
        )
        _jwt_auth_instance = JWTAuth(config)
    return _jwt_auth_instance


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
    """Create a signed JWT access token using forge-shared.

    Maintains backward compatibility with the previous API.
    Expects data to have 'sub' (user_id) key.
    """
    auth = get_jwt_auth_instance()
    user_id = data.get("sub")
    if not user_id:
        raise ValueError("Token data must include 'sub' (user_id)")

    # Create token with minimal forge-shared structure
    # Use defaults for optional fields since interview-simulator doesn't track them yet
    return auth.create_access_token(
        user_id=str(user_id),
        email=data.get("email", f"{user_id}@example.com"),
        domain="codeswiftr.com",
        plan=PlanTier.FREE,  # Interview-simulator uses its own subscription_tier
        products=["interview-simulator"],
        roles=[UserRole.USER],
        permissions=[Permission.READ_OWN, Permission.WRITE_OWN],
        extra_claims={k: v for k, v in data.items() if k not in ["sub", "email"]},
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token using forge-shared.

    Maintains backward compatibility with the previous API.
    Returns the payload as a dict or None if invalid.
    """
    try:
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(token)
        # Convert ForgeTokenPayload to dict for backward compatibility
        return {
            "sub": payload.sub,
            "email": payload.email,
            "exp": payload.exp,
            "iat": payload.iat,
        }
    except Exception:
        return None


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a JWT refresh token using forge-shared auth.

    Args:
        user_id: User ID to encode in the token

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    auth = get_jwt_auth_instance()
    token = auth.create_refresh_token(user_id=user_id)
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
    if datetime.now(UTC) > expires_at:
        return False
    # Verify JWT structure and signature
    try:
        auth = get_jwt_auth_instance()
        payload = auth.decode_token(provided_token)
        return payload.type == "refresh"
    except Exception:
        return False
