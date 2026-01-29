"""Unit tests for PostHog analytics service.

Tests the Analytics class methods without making actual API calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.analytics import Analytics, Events, get_analytics


class TestAnalyticsInit:
    """Tests for Analytics initialization."""

    def test_disabled_without_api_key(self):
        """Test analytics is disabled without API key."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None
            analytics = Analytics()
            assert analytics.enabled is False

    def test_enabled_with_api_key(self):
        """Test analytics is enabled with API key."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_api_key"
            mock_settings.posthog_host = "https://app.posthog.com"
            with patch("app.services.analytics.PostHogClient") as mock_client:
                analytics = Analytics()
                assert analytics.enabled is True
                mock_client.assert_called_once()


class TestGetUserId:
    """Tests for user ID formatting."""

    def test_formats_string_id(self):
        """Test formats string user ID."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None
            analytics = Analytics()

            result = analytics.get_user_id("user123")
            assert result == "forge_user123"

    def test_formats_int_id(self):
        """Test formats integer user ID."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None
            analytics = Analytics()

            result = analytics.get_user_id(12345)
            assert result == "forge_12345"


class TestGetBaseProperties:
    """Tests for base properties."""

    def test_includes_required_properties(self):
        """Test base properties include required fields."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None
            mock_settings.environment = "test"
            analytics = Analytics()

            props = analytics._get_base_properties()

            assert props["service"] == "interview-simulator-api"
            assert props["product"] == "interview-simulator"
            assert props["domain"] == "codeswiftr.com"
            assert props["environment"] == "test"


class TestCapture:
    """Tests for event capture."""

    def test_skips_when_disabled(self):
        """Test capture does nothing when analytics disabled."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None
            analytics = Analytics()

            analytics.capture("user123", "test_event", {"key": "value"})

    def test_captures_event_when_enabled(self):
        """Test captures event with properties when enabled."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_key"
            mock_settings.posthog_host = "https://app.posthog.com"
            mock_settings.environment = "test"

            mock_posthog = MagicMock()
            mock_posthog.track = AsyncMock()

            with patch("app.services.analytics.PostHogClient", return_value=mock_posthog):
                analytics = Analytics()
                analytics.capture("user123", "test_event", {"custom": "property"})

                mock_posthog.track.assert_awaited_once()
                call_kwargs = mock_posthog.track.call_args.kwargs
                assert call_kwargs["distinct_id"] == "forge_user123"
                assert call_kwargs["event"] == "test_event"
                assert "custom" in call_kwargs["properties"]
                assert call_kwargs["properties"]["custom"] == "property"

    def test_handles_capture_error_gracefully(self):
        """Test handles capture errors without raising."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_key"
            mock_settings.posthog_host = "https://app.posthog.com"
            mock_settings.environment = "test"

            mock_posthog = MagicMock()
            mock_posthog.track = AsyncMock(side_effect=Exception("API error"))

            with patch("app.services.analytics.PostHogClient", return_value=mock_posthog):
                analytics = Analytics()

                # Should not raise
                analytics.capture("user123", "test_event")

    def test_capture_without_properties(self):
        """Test captures event without custom properties."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_key"
            mock_settings.posthog_host = "https://app.posthog.com"
            mock_settings.environment = "test"

            mock_posthog = MagicMock()
            mock_posthog.track = AsyncMock()

            with patch("app.services.analytics.PostHogClient", return_value=mock_posthog):
                analytics = Analytics()
                analytics.capture("user123", "test_event")

                mock_posthog.track.assert_awaited_once()


class TestIdentify:
    """Tests for user identification."""

    def test_skips_when_disabled(self):
        """Test identify does nothing when analytics disabled."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None
            analytics = Analytics()

            analytics.identify("user123", {"email": "test@example.com"})

    def test_identifies_user_when_enabled(self):
        """Test identifies user with properties when enabled."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_key"
            mock_settings.posthog_host = "https://app.posthog.com"

            mock_posthog = MagicMock()
            mock_posthog.identify = AsyncMock()

            with patch("app.services.analytics.PostHogClient", return_value=mock_posthog):
                analytics = Analytics()
                analytics.identify("user123", {"email": "test@example.com", "tier": "pro"})

                mock_posthog.identify.assert_awaited_once()
                call_kwargs = mock_posthog.identify.call_args.kwargs
                assert call_kwargs["distinct_id"] == "forge_user123"
                assert call_kwargs["properties"]["email"] == "test@example.com"
                assert call_kwargs["properties"]["tier"] == "pro"
                assert call_kwargs["properties"]["product"] == "interview-simulator"

    def test_handles_identify_error_gracefully(self):
        """Test handles identify errors without raising."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_key"
            mock_settings.posthog_host = "https://app.posthog.com"

            mock_posthog = MagicMock()
            mock_posthog.identify = AsyncMock(side_effect=Exception("API error"))

            with patch("app.services.analytics.PostHogClient", return_value=mock_posthog):
                analytics = Analytics()

                # Should not raise
                analytics.identify("user123", {"email": "test@example.com"})


class TestShutdown:
    """Tests for analytics shutdown."""

    def test_shutdown_when_enabled(self):
        """Test shutdown calls posthog.shutdown when enabled."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = "test_key"
            mock_settings.posthog_host = "https://app.posthog.com"

            mock_posthog = MagicMock()

            with patch("app.services.analytics.PostHogClient", return_value=mock_posthog):
                analytics = Analytics()
                analytics.shutdown()
                mock_posthog.shutdown.assert_called_once()

    def test_shutdown_skips_when_disabled(self):
        """Test shutdown does nothing when disabled."""
        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None

            analytics = Analytics()
            analytics.shutdown()


class TestGetAnalytics:
    """Tests for singleton get_analytics function."""

    def test_returns_singleton(self):
        """Test returns same instance."""
        # Reset singleton
        import app.services.analytics as analytics_module

        analytics_module._analytics = None

        with patch("app.services.analytics.settings") as mock_settings:
            mock_settings.posthog_api_key = None

            first = get_analytics()
            second = get_analytics()

            assert first is second


class TestEvents:
    """Tests for event name constants."""

    def test_user_events_have_prefix(self):
        """Test user events have is_ prefix."""
        assert Events.USER_REGISTERED.startswith("is_")
        assert Events.USER_LOGGED_IN.startswith("is_")
        assert Events.USER_LOGGED_OUT.startswith("is_")
        assert Events.USER_VERIFIED.startswith("is_")

    def test_interview_events_have_prefix(self):
        """Test interview events have is_ prefix."""
        assert Events.INTERVIEW_CREATED.startswith("is_")
        assert Events.INTERVIEW_STARTED.startswith("is_")
        assert Events.INTERVIEW_COMPLETED.startswith("is_")
        assert Events.INTERVIEW_ABANDONED.startswith("is_")

    def test_subscription_events_have_prefix(self):
        """Test subscription events have is_ prefix."""
        assert Events.SUBSCRIPTION_CREATED.startswith("is_")
        assert Events.SUBSCRIPTION_UPGRADED.startswith("is_")
        assert Events.SUBSCRIPTION_CANCELED.startswith("is_")
        assert Events.PAYMENT_PROCESSED.startswith("is_")
        assert Events.PAYMENT_FAILED.startswith("is_")

    def test_all_events_follow_naming_convention(self):
        """Test all events follow is_{entity}_{action} convention."""
        event_attrs = [attr for attr in dir(Events) if not attr.startswith("_")]
        for attr in event_attrs:
            event_name = getattr(Events, attr)
            assert event_name.startswith("is_"), f"{attr} should start with 'is_'"
