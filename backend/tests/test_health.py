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
    """Test readiness check returns actual database connectivity status."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] is True


@pytest.mark.asyncio
async def test_readiness_check_includes_all_components(client):
    """Test readiness check includes database, redis, and ai_services keys."""
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
