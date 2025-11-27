"""Database session management for SQLModel."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    poolclass=NullPool,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables based on SQLModel metadata (used mainly for local/dev)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
