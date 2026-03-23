"""Gap-filling unit tests for health API.

Covers: version/environment keys in the detailed response, response_time_ms
in the Redis error dict, ConnectionError path in check_redis, and the
getattr fallback when openrouter_api_key is absent from settings.
No database required — all dependencies are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# health_detailed — version and environment keys
# ---------------------------------------------------------------------------


class TestHealthDetailedVersionAndEnvironment:
    @pytest.mark.asyncio
    async def test_health_detailed_includes_version_and_environment(self):
        """health_detailed must return 'version' and 'environment' keys in its
        response map regardless of the dependency states."""
        from app.api.health import health_detailed

        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.check_redis", new_callable=AsyncMock) as mock_redis,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_redis.return_value = True
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.environment = "staging"
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = None
            mock_settings.openrouter_api_key = None

            result = await health_detailed()

        assert "version" in result, "Expected 'version' key in health_detailed response"
        assert "environment" in result, "Expected 'environment' key in health_detailed response"
        assert result["environment"] == "staging"
        # Version is hardcoded in the source as "0.1.0"
        assert result["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# health_detailed — Redis error must include response_time_ms
# ---------------------------------------------------------------------------


class TestHealthDetailedRedisErrorResponseTime:
    @pytest.mark.asyncio
    async def test_health_detailed_redis_error_includes_response_time_ms(self):
        """When Redis is configured but unreachable, the 'redis' dict in the
        health_detailed response must contain a numeric 'response_time_ms' field."""
        from app.api.health import health_detailed

        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.check_redis", new_callable=AsyncMock) as mock_redis,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_redis.return_value = False  # Redis is down
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.environment = "test"
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = None
            mock_settings.openrouter_api_key = None

            result = await health_detailed()

        redis_info = result.get("redis", {})
        assert isinstance(redis_info, dict), "Expected 'redis' to be a dict"
        assert redis_info.get("status") == "error"
        assert "response_time_ms" in redis_info, (
            "Expected 'response_time_ms' in redis error dict"
        )
        assert isinstance(redis_info["response_time_ms"], (int, float))
        assert redis_info["response_time_ms"] >= 0


# ---------------------------------------------------------------------------
# check_redis — ConnectionError path returns False
# ---------------------------------------------------------------------------


class TestCheckRedisPingException:
    @pytest.mark.asyncio
    async def test_check_redis_ping_exception_returns_false(self):
        """When redis.ping() raises redis.ConnectionError, check_redis must
        catch it and return False instead of propagating the exception."""
        import redis as redis_lib

        from app.api.health import check_redis

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(
            side_effect=redis_lib.ConnectionError("Connection refused")
        )
        mock_client.aclose = AsyncMock()

        with (
            patch("app.api.health.settings") as mock_settings,
            patch("redis.asyncio.from_url", return_value=mock_client),
        ):
            mock_settings.redis_url = "redis://localhost:6379"
            result = await check_redis()

        assert result is False, (
            "check_redis must return False when ping raises ConnectionError"
        )


# ---------------------------------------------------------------------------
# check_ai_services — missing openrouter_api_key attribute (getattr fallback)
# ---------------------------------------------------------------------------


class TestCheckAIServicesMissingOpenrouterAttribute:
    def test_check_ai_services_missing_openrouter_attribute(self):
        """check_ai_services uses getattr(settings, 'openrouter_api_key', None),
        so deleting the attribute from a mock must not raise and must yield False
        for the 'openrouter' key."""
        from app.api.health import check_ai_services

        # Build a settings mock that has no openrouter_api_key attribute at all
        mock_settings = MagicMock(spec=["openai_api_key", "anthropic_api_key"])
        mock_settings.openai_api_key = "sk-test"
        mock_settings.anthropic_api_key = None

        with patch("app.api.health.settings", mock_settings):
            result = check_ai_services()

        # openai configured, anthropic not, openrouter attribute entirely absent
        assert result["openai"] is True
        assert result["anthropic"] is False
        # getattr fallback should evaluate to False (None or missing → bool(None) == False)
        assert result["openrouter"] is False, (
            "Missing openrouter_api_key attribute must resolve to False via getattr fallback"
        )
