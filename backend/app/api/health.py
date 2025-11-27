"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


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
