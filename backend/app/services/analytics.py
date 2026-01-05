"""PostHog analytics service for Interview Simulator event tracking."""

import logging
from typing import Any

import posthog

from app.config import settings

logger = logging.getLogger(__name__)


class Analytics:
    """Analytics service for PostHog event tracking.

    Provides unified analytics with consistent user identification
    and event properties following FORGE conventions.
    """

    def __init__(self) -> None:
        """Initialize PostHog with API key and host."""
        self._enabled = False
        if settings.posthog_api_key:
            posthog.project_api_key = settings.posthog_api_key
            posthog.host = settings.posthog_host
            posthog.disabled = False
            self._enabled = True
            logger.info("PostHog analytics initialized")
        else:
            logger.warning("PostHog API key not configured - analytics disabled")

    @property
    def enabled(self) -> bool:
        """Check if analytics is enabled."""
        return self._enabled

    def _get_base_properties(self) -> dict[str, Any]:
        """Get base properties included in all events."""
        return {
            "service": "interview-simulator-api",
            "product": "interview-simulator",
            "domain": "codeswiftr.com",
            "environment": settings.environment,
        }

    def get_user_id(self, user_id: str | int) -> str:
        """Format user ID for consistent identification across services."""
        return f"forge_{user_id}"

    def capture(
        self,
        user_id: str | int,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Capture an analytics event.

        Args:
            user_id: Internal user ID (will be prefixed with forge_)
            event: Event name (e.g., "interview_created", "payment_processed")
            properties: Additional event properties
        """
        if not self._enabled:
            return

        try:
            posthog.capture(
                distinct_id=self.get_user_id(user_id),
                event=event,
                properties={
                    **self._get_base_properties(),
                    **(properties or {}),
                },
            )
            logger.debug(f"Captured event '{event}' for user {user_id}")
        except Exception as e:
            # Don't fail the request if analytics fails
            logger.error(f"Failed to capture event: {e}")

    def identify(
        self,
        user_id: str | int,
        properties: dict[str, Any],
    ) -> None:
        """Identify a user with their properties.

        Call this on signup or when user properties change.

        Args:
            user_id: Internal user ID
            properties: User properties (email, tier, etc.)
        """
        if not self._enabled:
            return

        try:
            posthog.identify(
                distinct_id=self.get_user_id(user_id),
                properties={
                    **properties,
                    "product": "interview-simulator",
                    "domain": "codeswiftr.com",
                },
            )
            logger.debug(f"Identified user {user_id}")
        except Exception as e:
            logger.error(f"Failed to identify user: {e}")

    def shutdown(self) -> None:
        """Flush events and shutdown PostHog client."""
        if self._enabled:
            posthog.shutdown()
            logger.info("PostHog shutdown complete")


# Singleton instance
_analytics: Analytics | None = None


def get_analytics() -> Analytics:
    """Get or create singleton Analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = Analytics()
    return _analytics


# ============================================================================
# Event Names for Interview Simulator
# ============================================================================


class Events:
    """Standard event names for Interview Simulator tracking.

    All events use the 'is_' prefix for consistent identification
    across the FORGE analytics dashboard.

    Naming convention: is_{entity}_{action}
    Examples: is_interview_created, is_user_registered
    """

    # User Events
    USER_REGISTERED = "is_user_registered"
    USER_LOGGED_IN = "is_user_logged_in"
    USER_LOGGED_OUT = "is_user_logged_out"
    USER_VERIFIED = "is_user_verified"

    # Interview Events
    INTERVIEW_CREATED = "is_interview_created"
    INTERVIEW_STARTED = "is_interview_started"
    INTERVIEW_COMPLETED = "is_interview_completed"
    INTERVIEW_ABANDONED = "is_interview_abandoned"

    # Response Events
    RESPONSE_SUBMITTED = "is_response_submitted"
    TRANSCRIPTION_COMPLETED = "is_transcription_completed"

    # Feedback Events
    FEEDBACK_GENERATED = "is_feedback_generated"
    FEEDBACK_VIEWED = "is_feedback_viewed"

    # Subscription Events
    SUBSCRIPTION_CREATED = "is_subscription_created"
    SUBSCRIPTION_UPGRADED = "is_subscription_upgraded"
    SUBSCRIPTION_CANCELED = "is_subscription_canceled"
    PAYMENT_PROCESSED = "is_payment_processed"
    PAYMENT_FAILED = "is_payment_failed"
