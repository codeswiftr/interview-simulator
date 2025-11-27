"""Security utilities for password hashing and JWT handling."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


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
