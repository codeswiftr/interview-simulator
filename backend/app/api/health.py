"""Health check endpoints."""

import logging

from fastapi import APIRouter

from app.db import engine
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check() -> dict[str, str | bool]:
    """Readiness check including dependencies."""
    # TODO: Check database connection
    # TODO: Check Redis connection
    # TODO: Check AI service availability

    return {
        "status": "ready",
        "database": True,  # TODO: Actual check
        "redis": True,  # TODO: Actual check
        "ai_services": True,  # TODO: Actual check
    }


@router.get("/health/details")
async def health_detailed() -> dict[str, str]:
    """Detailed health check with dependency status.
    
    Returns status of database, Redis (if configured), and other critical services.
    Does not block the main health route.
    """
    status_map = {
        "status": "healthy",
    }
    
    # Check database connection
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        status_map["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status_map["database"] = "error"
        status_map["status"] = "degraded"
    
    # Check Redis (if configured)
    if settings.redis_url and settings.redis_url != "redis://localhost:6379/0":
        try:
            # Try to import redis and check connection
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url)
            await redis_client.ping()
            await redis_client.aclose()
            status_map["redis"] = "ok"
        except ImportError:
            status_map["redis"] = "not_configured"
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            status_map["redis"] = "error"
            status_map["status"] = "degraded"
    else:
        status_map["redis"] = "not_configured"
    
    # Check AI service keys (presence only, not actual API calls)
    ai_status = []
    if settings.openai_api_key:
        ai_status.append("openai")
    if settings.anthropic_api_key:
        ai_status.append("anthropic")
    
    status_map["ai_services"] = "configured" if ai_status else "not_configured"
    if not ai_status:
        status_map["status"] = "degraded"
    
    return status_map
