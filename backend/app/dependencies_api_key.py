"""API Key authentication dependencies.

Provides authentication via API keys in addition to JWT tokens.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models.user import User
from app.services import api_key_service

# Security scheme for API keys
api_key_scheme = HTTPBearer(auto_error=False, scheme_name="API Key")


async def get_user_from_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(api_key_scheme),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Get user from API key authentication.

    Checks for API key in Authorization header:
    - Format: Authorization: Bearer is_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    Args:
        credentials: HTTP authorization credentials
        session: Database session

    Returns:
        User if API key is valid, None otherwise
    """
    if credentials is None:
        return None

    api_key = credentials.credentials

    # Verify it's an API key (starts with 'is_')
    if not api_key.startswith("is_"):
        return None

    # Verify the key and get the user
    user = await api_key_service.verify_api_key_and_get_user(session, api_key)
    return user


async def require_api_key(
    user: Annotated[User | None, Depends(get_user_from_api_key)],
) -> User:
    """Require valid API key authentication.

    Args:
        user: User from API key authentication

    Returns:
        Authenticated user

    Raises:
        HTTPException 401: If API key is invalid or missing
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_user_flexible(
    credentials: HTTPAuthorizationCredentials | None = Depends(api_key_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Authenticate user via either JWT token or API key.

    This dependency allows endpoints to accept both JWT and API key authentication.

    Args:
        credentials: HTTP authorization credentials
        session: Database session

    Returns:
        Authenticated user

    Raises:
        HTTPException 401: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check if it's an API key (starts with 'is_')
    if token.startswith("is_"):
        user = await api_key_service.verify_api_key_and_get_user(session, token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    # Otherwise, treat as JWT token
    from app.dependencies import get_current_user
    from forge_shared.auth.dependencies import get_jwt_auth

    auth = await get_jwt_auth()

    try:
        payload = auth.decode_token(token)
        user_id: str = payload.sub
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    from sqlmodel import select

    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
