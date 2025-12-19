"""Tests for configuration and environment validation."""

import pytest

from app.config import Settings


def test_settings_requires_critical_env_in_production(monkeypatch):
    """Test that settings validation raises error for missing critical env vars in production."""
    # Set debug to False (production mode)
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg:/postgres:postgres@localhost:5432/test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("SECRET_KEY", "change-me-in-production")

    # Clear cache to force reload
    Settings.model_config["env_file"] = None
    from app.config import get_settings
    get_settings.cache_clear()

    settings = get_settings()

    # Should raise ValueError in production
    with pytest.raises(ValueError, match="Missing required environment variables"):
        settings.validate_for_production()


def test_settings_allows_missing_optional_env_in_debug(monkeypatch):
    """Test that settings validation allows missing optional vars in debug mode."""
    # Set debug to True
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg:/postgres:postgres@localhost:5432/test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    # Clear cache
    from app.config import get_settings
    get_settings.cache_clear()

    settings = get_settings()

    # Should not raise in debug mode
    try:
        settings.validate_for_production()
    except ValueError:
        pytest.fail("validate_for_production() should not raise in debug mode")

