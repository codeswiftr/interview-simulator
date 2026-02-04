"""FastAPI application entry point for Interview Simulator.

Migrated to use forge-shared middleware (2025-01).
"""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from forge_shared.analytics import AnalyticsMiddleware
from forge_shared.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityMiddleware,
)
from forge_shared.utm import UTMMiddleware

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
from app.exceptions import AppError


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

    # Email service configuration validation
    if settings.resend_api_key:
        from_email = settings.resend_from_email
        # Validate from_email is not sandbox/test email
        if not from_email or "resend.dev" in from_email:
            logger.error(
                f"CRITICAL: RESEND_FROM_EMAIL is set to sandbox value '{from_email}'. "
                "Password reset emails will fail. Set to a verified domain like 'hello@codeswiftr.com'"
            )
        elif "@" not in from_email:
            logger.error(f"CRITICAL: RESEND_FROM_EMAIL '{from_email}' is not a valid email address")
        else:
            logger.info(f"Email configured: Resend (from: {from_email})")
    else:
        logger.warning("RESEND_API_KEY not configured - password reset emails will not be sent")

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
    redirect_slashes=False,  # Prevent 307 redirects that break CORS
)


def custom_openapi():
    """Custom OpenAPI schema with JWT Bearer authentication."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add JWT Bearer security scheme
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}

    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT access token obtained from /api/v1/auth/login endpoint",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Exception handler for structured AppError exceptions
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert AppError exceptions to structured JSON responses.

    All AppError subclasses are automatically converted to consistent
    error responses with machine-readable codes and user-friendly messages.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


# forge-shared middleware (migrated from custom implementations)
# UTMMiddleware for attribution tracking
app.add_middleware(UTMMiddleware)

# RequestIDMiddleware replaces custom CorrelationIDMiddleware
app.add_middleware(RequestIDMiddleware)

# SecurityMiddleware replaces custom SecurityHeadersMiddleware
app.add_middleware(SecurityMiddleware, x_frame_options="DENY")

# Analytics middleware for PostHog tracking
posthog_api_key = getattr(settings, "posthog_api_key", None)
if posthog_api_key:
    app.add_middleware(
        AnalyticsMiddleware,
        api_key=posthog_api_key,
        host=getattr(settings, "posthog_host", "https://app.posthog.com"),
    )

# CORS configuration - restricted for security
# In development: allow localhost on any port via regex
# In production: use explicit origins list (localhost origins excluded automatically)
origins = settings.effective_cors_origins
allow_origin_regex = None

if settings.debug:
    # Development: allow localhost on any port + .local domains (Caddy proxy)
    allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1|[\w.-]+\.local)(:\d+)?$"
    origins = []  # Use regex instead of explicit list
else:
    # In production, ensure no wildcard origins
    if "*" in origins or "http://*" in origins or "https://*" in origins:
        logging.error("CORS origins contain wildcards in production - this is a security risk")
        raise ValueError("Wildcard CORS origins are not allowed in production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],
    expose_headers=["X-Correlation-ID"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Rate limiting with forge-shared RateLimitMiddleware (only in production)
if not settings.debug:
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.redis_url,
        requests_per_minute=60,
        requests_per_hour=1000,
        exclude_paths=["/api/v1/health", "/docs", "/openapi.json", "/", "/favicon.ico", "/static"],
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
