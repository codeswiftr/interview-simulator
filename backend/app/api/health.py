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
async def health_detailed() -> dict[str, str]:
    """Detailed health check with dependency status.

    Returns status of database, Redis (if configured), and other critical services.
    Does not block the main health route.
    """
    status_map: dict[str, str] = {
        "status": "healthy",
    }

    # Check database connection
    db_ok = await check_db_connection()
    if db_ok:
        status_map["database"] = "ok"
    else:
        logger.error("Database health check failed")
        status_map["database"] = "error"
        status_map["status"] = "degraded"

    # Check Redis (if configured)
    if settings.redis_url:
        redis_ok = await check_redis()
        if redis_ok:
            status_map["redis"] = "ok"
        else:
            status_map["redis"] = "error"
            status_map["status"] = "degraded"
    else:
        status_map["redis"] = "not_configured"

    # Check AI service keys (presence only, not actual API calls)
    ai_services = check_ai_services()
    if ai_services["openai"] or ai_services["anthropic"]:
        configured = []
        if ai_services["openai"]:
            configured.append("openai")
        if ai_services["anthropic"]:
            configured.append("anthropic")
        status_map["ai_services"] = f"configured ({', '.join(configured)})"
    else:
        status_map["ai_services"] = "not_configured"
        status_map["status"] = "degraded"

    return status_map
