"""FastAPI application entry point for Interview Simulator.

Migrated to use forge-shared middleware (2025-01).
Phase 2.2: BackgroundTasks replaced by forge-jobs DB-backed queue (2026-03).
"""

import asyncio
import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from forge_shared.jobs import JobQueue
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from forge_shared.analytics import AnalyticsMiddleware, ConversionTracker, set_conversion_tracker
from forge_shared.middleware import (
    RequestIDMiddleware,
    SecurityMiddleware,
)
from forge_shared.utm import UTMMiddleware

from app.middleware.pg_rate_limit import PgRateLimitMiddleware

from app.api import (
    analytics,
    api_keys,
    auth,
    coaching,
    feedback,
    health,
    interviews,
    preparation,
    questions,
    subscriptions,
    teams,
    transcription,
    upload,
    users,
)
from app.config import settings
from app.data.seed_questions import seed_questions
from app.db import SessionLocal, check_db_connection, close_db_connections
from app.exceptions import AppError


class _EmailMaskingFilter(logging.Filter):
    """Log filter that masks email addresses in all log records.

    Prevents PII leakage through log output by replacing any email
    address found in the log message with a masked equivalent.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        from app.utils.log_utils import mask_emails_in_text

        record.msg = mask_emails_in_text(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: mask_emails_in_text(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            else:
                record.args = tuple(
                    mask_emails_in_text(str(a)) if isinstance(a, str) else a for a in record.args
                )
        return True


def configure_logging() -> None:
    """Configure structured logging for the application.

    Sets up JSON-formatted logging in production, simple format in development.
    Attaches the EmailMaskingFilter to prevent PII leakage.
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

    # Attach email masking filter to the root logger so all log records
    # produced by the application have PII stripped before output.
    email_filter = _EmailMaskingFilter()
    logging.getLogger().addFilter(email_filter)

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

    # Initialize forge-auth (ForgeAuth facade — S152 Week 2)
    from app.security import get_forge_auth_instance

    get_forge_auth_instance()  # Eagerly create the singleton on startup
    logger.info("Initialized forge-auth (ForgeAuth) JWT authentication")

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

    # Initialize ConversionTracker for Stripe revenue attribution (no Redis required)
    try:
        from app.services.analytics import get_analytics

        analytics_service = get_analytics()
        posthog_client = analytics_service._client
        if posthog_client:
            conversion_tracker = ConversionTracker(
                posthog_client=posthog_client,
                redis_client=None,  # Redis dropped — Phase 1.1
            )
            set_conversion_tracker(conversion_tracker)
            logger.info("ConversionTracker initialized for Stripe revenue attribution")
        else:
            logger.warning(
                "PostHog client not available — ConversionTracker not initialized"
            )
    except Exception as e:
        logger.warning(f"ConversionTracker initialization failed (non-critical): {e}")

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

    # Initialize forge-jobs DB-backed queue and start background worker
    from app.api.interviews import set_job_queue
    from app.services.job_handlers import (
        handle_generate_feedback,
        handle_generate_session_feedback,
        handle_process_audio,
    )

    job_queue = JobQueue(str(settings.database_url))
    await job_queue.init()
    set_job_queue(job_queue)
    logger.info("forge-jobs queue initialized")

    worker_task = asyncio.create_task(
        job_queue.run_worker(
            handlers={
                "process_audio": handle_process_audio,
                "generate_feedback": handle_generate_feedback,
                "generate_session_feedback": handle_generate_session_feedback,
            },
            poll_interval=2.0,
        )
    )
    logger.info("forge-jobs worker started (poll_interval=2s)")

    yield

    # Shutdown worker and close queue connection
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await job_queue.close()
    set_job_queue(None)
    logger.info("forge-jobs worker stopped")

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

# SecurityMiddleware: explicit hardened security header configuration
# All required headers are set explicitly so future forge-shared default changes
# do not silently weaken production security posture.
app.add_middleware(
    SecurityMiddleware,
    x_frame_options="DENY",
    hsts_enabled=True,
    hsts_max_age=31536000,  # 1 year
    hsts_include_subdomains=True,
    x_content_type_options="nosniff",
    x_xss_protection="1; mode=block",
    referrer_policy="strict-origin-when-cross-origin",
)

# Analytics middleware for PostHog tracking
posthog_api_key = getattr(settings, "posthog_api_key", None)
if posthog_api_key:
    app.add_middleware(
        AnalyticsMiddleware,
        posthog_api_key=posthog_api_key,
        posthog_host=getattr(settings, "posthog_host", "https://app.posthog.com"),
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
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "X-Request-ID"],
    expose_headers=["X-Correlation-ID"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Rate limiting with PostgreSQL-backed middleware (only in production)
if not settings.debug:
    app.add_middleware(
        PgRateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000,
        exclude_paths=["/health", "/docs", "/openapi.json", "/", "/favicon.ico", "/static"],
    )

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["API Keys"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["Interviews"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(transcription.router, prefix="/api/v1/transcription", tags=["Transcription"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(coaching.router, prefix="/api/v1/coaching", tags=["Coaching"])
app.include_router(preparation.router, prefix="/api/v1/preparation", tags=["Preparation"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])

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
