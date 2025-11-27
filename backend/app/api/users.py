"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies import get_current_user
from app.db import get_session
from app.models.user import Token, User, UserCreate, UserLogin, UserRead
from app.security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    """Register a new user."""
    existing = await session.exec(select(User).where(User.email == payload.email))
    if existing.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, session: AsyncSession = Depends(get_session)) -> Token:
    """Authenticate user and return access token."""
    result = await session.exec(select(User).where(User.email == payload.email.lower()))
    user = result.first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user."""
    return current_user
