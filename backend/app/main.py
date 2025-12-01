"""FastAPI application entry point for Interview Simulator."""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import feedback, health, interviews, questions, subscriptions, transcription, upload, users
from app.config import settings
from app.data.seed_questions import seed_questions
from app.db import SessionLocal
from app.middleware.rate_limit import RateLimitConfig, RateLimitMiddleware


def configure_logging() -> None:
    """Configure structured logging for the application.
    
    Sets up JSON-formatted logging in production, simple format in development.
    """
    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if settings.debug
        else "%(asctime)s [%(levelname)s] %(name)s [%(correlation_id)s]: %(message)s"
    )
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if not settings.debug else logging.INFO)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests for log tracing."""
    
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        logger = logging.getLogger(__name__)
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = correlation_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            logging.setLogRecordFactory(old_factory)


def init_error_monitoring() -> None:
    """Initialize error monitoring (Sentry) if configured.
    
    Only initializes if SENTRY_DSN is set in environment.
    """
    sentry_dsn = getattr(settings, "sentry_dsn", None)
    if sentry_dsn and not settings.debug:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                ],
                traces_sample_rate=0.1,
                environment=settings.environment,
            )
            logging.getLogger(__name__).info("Sentry error monitoring initialized")
        except ImportError:
            logging.getLogger(__name__).warning("Sentry SDK not installed, skipping error monitoring")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Configure logging first
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Validate environment for production
    try:
        settings.validate_for_production()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        if not settings.debug:
            raise  # Fail fast in production
    
    # Initialize error monitoring
    init_error_monitoring()
    
    # Startup
    logger.info(f"Starting Interview Simulator v{app.version}")
    # TODO: Initialize database connections
    # TODO: Initialize Redis connection
    # TODO: Warm up AI models
    # Seed data in debug/local environments
    if settings.debug:
        async with SessionLocal() as session:
            await seed_questions(session)

    yield

    # Shutdown
    logger.info("Shutting down Interview Simulator")
    # TODO: Close database connections
    # TODO: Close Redis connection


app = FastAPI(
    title="CareerSwiftr Interview Simulator",
    description="AI-powered interview practice platform for software engineers",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Correlation ID middleware (add early for request tracing)
app.add_middleware(CorrelationIDMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (only in production)
if not settings.debug:
    app.add_middleware(
        RateLimitMiddleware,
        config=RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
        ),
        exclude_paths=["/api/v1/health", "/docs", "/openapi.json", "/"],
    )

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["Interviews"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(transcription.router, prefix="/api/v1/transcription", tags=["Transcription"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])

# Mount static files for uploaded content
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "CareerSwiftr Interview Simulator",
        "version": "0.1.0",
        "docs": "/docs",
    }
