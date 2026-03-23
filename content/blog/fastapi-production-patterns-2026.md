---
title: "FastAPI Production Patterns 2026"
description: "Battle-tested FastAPI patterns for production—dependency injection, async SQLAlchemy, background tasks, middleware, error handling, and the architecture patterns used in high-traffic FastAPI services."
date: "2026-03-21"
category: "Language Deep Dives"
---

# FastAPI Production Patterns 2026

FastAPI has become the dominant Python web framework for new API development. Its combination of Pydantic validation, OpenAPI documentation, async support, and developer experience is unmatched. This guide covers the production patterns that distinguish robust FastAPI applications from quick prototypes.

## Application Factory Pattern

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import users, posts, auth
from app.infrastructure.database import engine
from app.middleware import setup_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await engine.connect()
    yield
    # Shutdown
    await engine.disconnect()

def create_app() -> FastAPI:
    app = FastAPI(
        title="My API",
        version="1.0.0",
        lifespan=lifespan
    )
    setup_middleware(app)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(posts.router, prefix="/api/v1")
    return app

app = create_app()
```

## Dependency Injection for Database Sessions

```python
# app/infrastructure/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=0)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

```python
# In router
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Authentication Dependencies

```python
# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user
```

## Global Exception Handler

```python
# app/middleware/error_handling.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content={"detail": "Resource conflict", "code": "CONFLICT"}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
```

## Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/users/", status_code=201)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user = User(**user_data.model_dump())
    db.add(user)
    await db.flush()  # Get the ID before commit

    # Add background task — runs after response is sent
    background_tasks.add_task(send_welcome_email, user.id, user.email)
    background_tasks.add_task(setup_user_preferences, user.id)

    await db.commit()
    await db.refresh(user)
    return user
```

For heavy background work, use Celery or ARQ instead of FastAPI's built-in BackgroundTasks (which runs in the same process).

## Middleware for Request Tracking

```python
from fastapi import FastAPI, Request
import uuid
import time
import logging

logger = logging.getLogger(__name__)

async def request_tracking_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )
    response.headers["X-Request-ID"] = request_id
    return response
```

## Pydantic v2 Response Models

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode

    id: int
    username: str
    email: str
    created_at: datetime

    # Computed field
    @computed_field
    @property
    def display_name(self) -> str:
        return self.username.title()

# In router — FastAPI validates the response against the model
@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    return await db.get(User, id)
```

## Interview Tips

FastAPI interview questions for senior roles:

1. **Dependency injection system** — how DI chains work, `Depends()` nesting
2. **Async SQLAlchemy** — proper session management with context managers
3. **Lifespan events** — startup/shutdown resource management
4. **Pydantic v2 patterns** — `model_config`, `computed_field`, validation
5. **Background tasks vs Celery** — when each is appropriate

The most impressive FastAPI knowledge: understanding that dependencies are resolved lazily and cached within a request, and how that interacts with `AsyncSession` lifecycle to ensure proper transaction management.
