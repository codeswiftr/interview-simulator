"""Common FastAPI dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models.user import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    """Retrieve current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if user is None:
        raise credentials_exception
    return user
