"""Simple feature flag utilities for conditional endpoints."""

from fastapi import HTTPException, status

from app.config import settings


def require_video_features_enabled() -> None:
    """Ensure video-related functionality is enabled."""
    if not settings.video_features_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review is not available during soft launch.",
        )
