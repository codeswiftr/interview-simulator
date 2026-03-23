"""Health check endpoints."""

import logging

from fastapi import APIRouter, Response, status

from app.config import settings
from app.db import check_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)


async def check_redis() -> bool:
    """Check Redis connectivity by executing PING.

    Returns:
        True if Redis is reachable, False otherwise.
    """
    if not settings.redis_url:
        return False
    try:
        import redis.asyncio as redis

        redis_client = redis.from_url(settings.redis_url, socket_timeout=5.0)
        await redis_client.ping()
        await redis_client.aclose()
        return True
    except ImportError:
        logger.warning("Redis package not installed")
        return False
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


def check_ai_services() -> dict[str, bool]:
    """Check if AI service API keys are configured.

    Returns:
        Dict with service names and their configuration status.
    """
    return {
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "openrouter": bool(getattr(settings, "openrouter_api_key", None)),
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint (always returns healthy if app is running)."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check(response: Response) -> dict[str, str | bool]:
    """Readiness check including actual dependency connectivity.

    Returns HTTP 503 if database is unreachable (critical dependency).
    Redis and AI services are optional - their absence degrades but doesn't fail.
    """
    db_ok = await check_db_connection()
    redis_ok = await check_redis()
    ai_services = check_ai_services()
    ai_configured = ai_services["openai"] or ai_services["anthropic"]

    # Database is critical - fail readiness if DB is down
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": False,
            "redis": redis_ok,
            "ai_services": ai_configured,
        }

    return {
        "status": "ready",
        "database": True,
        "redis": redis_ok,
        "ai_services": ai_configured,
    }


@router.get("/health/details")
async def health_detailed() -> dict[str, str | dict]:
    """Detailed health check with dependency status.

    Returns comprehensive status of all dependencies including response times.
    Does not block the main health route.
    """
    import time

    status_map: dict[str, str | dict] = {
        "status": "healthy",
    }

    # Check database connection with timing
    db_start = time.time()
    db_ok = await check_db_connection()
    db_time = (time.time() - db_start) * 1000  # Convert to ms

    if db_ok:
        status_map["database"] = {
            "status": "ok",
            "response_time_ms": round(db_time, 2),
        }
    else:
        logger.error("Database health check failed")
        status_map["database"] = {
            "status": "error",
            "response_time_ms": round(db_time, 2),
        }
        status_map["status"] = "degraded"

    # Check Redis (if configured) with timing
    if settings.redis_url:
        redis_start = time.time()
        redis_ok = await check_redis()
        redis_time = (time.time() - redis_start) * 1000

        if redis_ok:
            status_map["redis"] = {
                "status": "ok",
                "response_time_ms": round(redis_time, 2),
            }
        else:
            status_map["redis"] = {
                "status": "error",
                "response_time_ms": round(redis_time, 2),
            }
            status_map["status"] = "degraded"
    else:
        status_map["redis"] = {"status": "not_configured"}

    # Check AI service keys (presence only, not actual API calls)
    ai_services = check_ai_services()
    configured = []
    if ai_services["openai"]:
        configured.append("openai")
    if ai_services["anthropic"]:
        configured.append("anthropic")
    if ai_services.get("openrouter"):
        configured.append("openrouter")

    if configured:
        status_map["ai_services"] = {
            "status": "configured",
            "providers": configured,
        }
    else:
        status_map["ai_services"] = {
            "status": "not_configured",
            "providers": [],
        }
        status_map["status"] = "degraded"

    # Add version and environment info
    status_map["version"] = "0.1.0"
    status_map["environment"] = settings.environment

    return status_map
