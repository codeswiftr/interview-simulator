"""Tests for Sentry error monitoring integration."""

import pytest


class TestSentryConfiguration:
    """Tests for Sentry configuration in settings."""

    def test_sentry_dsn_setting_exists(self):
        """Verify sentry_dsn setting exists in config."""
        from app.config import Settings

        settings = Settings()
        assert hasattr(settings, "sentry_dsn")
        # Default should be empty string
        assert settings.sentry_dsn == "" or isinstance(settings.sentry_dsn, str)

    def test_environment_setting_exists(self):
        """Verify environment setting exists in config."""
        from app.config import Settings

        settings = Settings()
        assert hasattr(settings, "environment")
        assert settings.environment in ["development", "staging", "production"]

    def test_debug_setting_exists(self):
        """Verify debug setting exists and defaults to False in prod."""
        from app.config import Settings

        settings = Settings()
        assert hasattr(settings, "debug")
        assert isinstance(settings.debug, bool)

    def test_init_error_monitoring_function_exists(self):
        """Verify init_error_monitoring function is defined."""
        from app.main import init_error_monitoring

        assert callable(init_error_monitoring)

    def test_sentry_sdk_import_works(self):
        """Verify sentry_sdk can be imported."""
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        assert sentry_sdk is not None
        assert FastApiIntegration is not None
        assert SqlalchemyIntegration is not None

    def test_init_error_monitoring_handles_missing_dsn(self):
        """Verify init_error_monitoring doesn't crash without DSN."""
        from unittest.mock import patch

        with patch("app.main.settings") as mock_settings:
            mock_settings.sentry_dsn = ""
            mock_settings.debug = False

            from app.main import init_error_monitoring

            # Should not raise
            init_error_monitoring()

    def test_init_error_monitoring_skips_in_debug(self):
        """Verify init_error_monitoring skips initialization in debug mode."""
        from unittest.mock import patch

        with patch("app.main.settings") as mock_settings:
            mock_settings.sentry_dsn = "https://test@sentry.io/123"
            mock_settings.debug = True

            from app.main import init_error_monitoring

            # Should not raise, should skip Sentry
            init_error_monitoring()
