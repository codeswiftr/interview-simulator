"""FastAPI application entry point for Interview Simulator."""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import (
    auth,
    coaching,
    feedback,
    health,
    interviews,
    preparation,
    questions,
    subscriptions,
    transcription,
    upload,
    users,
)
from app.config import settings
from app.data.seed_questions import seed_questions
from app.db import SessionLocal, check_db_connection, close_db_connections
from app.middleware.rate_limit import RateLimitConfig, RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


def configure_logging() -> None:
    """Configure structured logging for the application.

    Sets up JSON-formatted logging in production, simple format in development.
    """
    log_level = logging.DEBUG if settings.debug else logging.INFO

    if settings.debug:
        # Development: Human-readable format
        handler = logging.StreamHandler(sys.stdout)
    else:
        # Production: JSON-structured logging
        import json
        from datetime import datetime

        class JSONFormatter(logging.Formatter):
            """JSON formatter for structured logging in production."""

            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }

                # Add correlation ID if available
                if hasattr(record, "correlation_id"):
                    log_data["correlation_id"] = record.correlation_id

                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)

                # Add extra fields
                if hasattr(record, "extra"):
                    log_data.update(record.extra)

                return json.dumps(log_data)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if not settings.debug else logging.INFO
    )


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests for log tracing."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        request.state.correlation_id = correlation_id

        # Add to logging context
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
            logging.getLogger(__name__).warning(
                "Sentry SDK not installed, skipping error monitoring"
            )


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

    # Verify database connection
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("Database connection verified")
    else:
        logger.error("Database connection failed!")
        if not settings.debug:
            raise RuntimeError("Cannot start: database unreachable")

    # Verify Redis connection (optional)
    try:
        import redis.asyncio as redis

        redis_client = redis.from_url(settings.redis_url, socket_timeout=5.0)
        await redis_client.ping()
        await redis_client.aclose()
        logger.info("Redis connection verified")
    except ImportError:
        logger.warning("Redis package not installed, skipping")
    except Exception as e:
        logger.warning(f"Redis connection failed (non-critical): {e}")

    # Check AI services configuration based on selected providers
    # Transcription provider check
    if settings.transcription_provider == "groq":
        if settings.groq_api_key:
            logger.info("Transcription configured: Groq (whisper-large-v3)")
        else:
            logger.warning("Groq API key not configured - transcription will fail")
    else:
        if settings.openai_api_key:
            logger.info("Transcription configured: OpenAI (whisper-1)")
        else:
            logger.warning("OpenAI API key not configured - transcription will fail")

    # Content analysis provider check
    if settings.content_analysis_provider == "openrouter":
        if settings.openrouter_api_key:
            logger.info("Content analysis configured: OpenRouter (Claude)")
        else:
            logger.warning("OpenRouter API key not configured - feedback generation will fail")
    else:
        if settings.anthropic_api_key:
            logger.info("Content analysis configured: Anthropic (Claude)")
        else:
            logger.warning("Anthropic API key not configured - feedback generation will fail")

    # Seed data in debug/local environments
    if settings.debug:
        async with SessionLocal() as session:
            await seed_questions(session)

    yield

    # Shutdown
    logger.info("Shutting down Interview Simulator")
    await close_db_connections()
    logger.info("Database connections closed")


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

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["Interviews"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(transcription.router, prefix="/api/v1/transcription", tags=["Transcription"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(coaching.router, prefix="/api/v1/coaching", tags=["Coaching"])
app.include_router(preparation.router, prefix="/api/v1/preparation", tags=["Preparation"])

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
