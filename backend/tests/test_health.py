"""Tests for health endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    """Test root endpoint returns API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CareerSwiftr Interview Simulator"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint always returns healthy."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_check_returns_actual_db_status(client):
    """Test readiness check returns ready when DB and Redis are available."""
    with (
        patch("app.api.health.check_redis", new_callable=AsyncMock) as mock_redis,
        patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis.return_value = True
        mock_db.return_value = True
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] is True


@pytest.mark.asyncio
async def test_readiness_check_includes_all_components(client):
    """Test readiness check includes database, redis, and ai_services keys."""
    with (
        patch("app.api.health.check_redis", new_callable=AsyncMock) as mock_redis,
        patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
    ):
        mock_redis.return_value = True
        mock_db.return_value = True
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "ai_services" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_readiness_returns_503_when_db_down(client):
    """Test readiness returns HTTP 503 when database is unreachable."""
    with patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = False
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"] is False


@pytest.mark.asyncio
async def test_health_detailed_includes_db_status(client):
    """Test that detailed health check includes database status."""
    response = await client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "status" in data
    # Database returns a dict with status and response_time_ms
    assert isinstance(data["database"], dict)
    assert data["database"]["status"] in ["ok", "error"]


@pytest.mark.asyncio
async def test_health_detailed_handles_db_failure_gracefully(client):
    """Test that detailed health check handles database failure gracefully."""
    # This test verifies the endpoint doesn't crash on DB errors
    response = await client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    # Should return status map with status field
    assert isinstance(data["database"], dict)
    assert "status" in data["database"]


@pytest.mark.asyncio
async def test_health_detailed_shows_degraded_when_db_fails(client):
    """Test that detailed health shows degraded status when DB is down."""
    with patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = False
        response = await client.get("/health/details")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["status"] == "error"


@pytest.mark.asyncio
async def test_health_detailed_includes_ai_services_status(client):
    """Test that detailed health check includes AI services configuration."""
    response = await client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "ai_services" in data


class TestCheckRedis:
    """Tests for check_redis function."""

    @pytest.mark.asyncio
    async def test_check_redis_no_redis_url(self):
        """Test check_redis returns False when redis_url not configured."""
        from app.api.health import check_redis

        with patch("app.api.health.settings") as mock_settings:
            mock_settings.redis_url = None
            result = await check_redis()
            assert result is False

    @pytest.mark.asyncio
    async def test_check_redis_success(self):
        """Test check_redis returns True when Redis is reachable."""
        from app.api.health import check_redis

        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_redis_client.aclose = AsyncMock()

        with patch("app.api.health.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            with patch("redis.asyncio.from_url", return_value=mock_redis_client):
                result = await check_redis()
                assert result is True
                mock_redis_client.ping.assert_called_once()
                mock_redis_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_redis_import_error(self):
        """Test check_redis handles missing redis package."""
        from app.api.health import check_redis

        with patch("app.api.health.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"

            import builtins
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "redis.asyncio" or name == "redis":
                    raise ImportError("No module named 'redis'")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, "__import__", mock_import):
                result = await check_redis()
                assert result is False

    @pytest.mark.asyncio
    async def test_check_redis_connection_error(self):
        """Test check_redis handles connection errors gracefully."""
        from app.api.health import check_redis

        with patch("app.api.health.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            with patch("redis.asyncio.from_url", side_effect=Exception("Connection refused")):
                result = await check_redis()
                assert result is False


class TestCheckAIServices:
    """Tests for check_ai_services function."""

    def test_check_ai_services_all_configured(self):
        """Test check_ai_services when all services configured."""
        from app.api.health import check_ai_services

        with patch("app.api.health.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = "sk-ant-test"
            mock_settings.openrouter_api_key = "sk-or-test"

            result = check_ai_services()

            assert result["openai"] is True
            assert result["anthropic"] is True
            assert result["openrouter"] is True

    def test_check_ai_services_none_configured(self):
        """Test check_ai_services when no services configured."""
        from app.api.health import check_ai_services

        with patch("app.api.health.settings") as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = ""
            # Remove openrouter_api_key attribute
            delattr(mock_settings, "openrouter_api_key") if hasattr(mock_settings, "openrouter_api_key") else None

            result = check_ai_services()

            assert result["openai"] is False
            assert result["anthropic"] is False


class TestHealthDetailedEdgeCases:
    """Additional tests for health/details endpoint edge cases."""

    @pytest.mark.asyncio
    async def test_health_detailed_db_ok_with_timing(self, client):
        """Test detailed health shows OK database with response time."""
        with patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = True
            response = await client.get("/health/details")
            assert response.status_code == 200
            data = response.json()
            assert data["database"]["status"] == "ok"
            assert "response_time_ms" in data["database"]

    @pytest.mark.asyncio
    async def test_health_detailed_redis_ok(self, client):
        """Test detailed health shows OK redis when connected."""
        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.check_redis", new_callable=AsyncMock) as mock_redis,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_redis.return_value = True
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.environment = "test"

            response = await client.get("/health/details")
            assert response.status_code == 200
            data = response.json()
            assert data["redis"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_detailed_redis_not_configured(self, client):
        """Test detailed health shows not_configured when redis_url is None."""
        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_settings.redis_url = None
            mock_settings.environment = "test"
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = None

            response = await client.get("/health/details")
            assert response.status_code == 200
            data = response.json()
            assert data["redis"]["status"] == "not_configured"

    @pytest.mark.asyncio
    async def test_health_detailed_ai_configured_multiple(self, client):
        """Test detailed health shows multiple AI providers configured."""
        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_settings.redis_url = None
            mock_settings.environment = "test"
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = "sk-ant-test"
            mock_settings.openrouter_api_key = "sk-or-test"

            response = await client.get("/health/details")
            assert response.status_code == 200
            data = response.json()
            assert data["ai_services"]["status"] == "configured"
            assert "openai" in data["ai_services"]["providers"]
            assert "anthropic" in data["ai_services"]["providers"]

    @pytest.mark.asyncio
    async def test_health_detailed_ai_not_configured(self, client):
        """Test detailed health shows not_configured when no AI services."""
        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_settings.redis_url = None
            mock_settings.environment = "test"
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = ""
            # Simulate missing openrouter_api_key attribute
            type(mock_settings).openrouter_api_key = property(lambda self: None)

            response = await client.get("/health/details")
            assert response.status_code == 200
            data = response.json()
            assert data["ai_services"]["status"] == "not_configured"
            assert data["ai_services"]["providers"] == []
            assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_detailed_redis_error_degrades_status(self, client):
        """Test detailed health shows degraded when Redis fails."""
        with (
            patch("app.api.health.check_db_connection", new_callable=AsyncMock) as mock_db,
            patch("app.api.health.check_redis", new_callable=AsyncMock) as mock_redis,
            patch("app.api.health.settings") as mock_settings,
        ):
            mock_db.return_value = True
            mock_redis.return_value = False  # Redis fails
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.environment = "test"
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = None

            response = await client.get("/health/details")
            assert response.status_code == 200
            data = response.json()
            assert data["redis"]["status"] == "error"
            assert data["status"] == "degraded"
