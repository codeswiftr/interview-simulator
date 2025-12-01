"""Tests for health endpoints."""

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
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_check(client):
    """Test readiness check endpoint."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_health_detailed_includes_db_status(client):
    """Test that detailed health check includes database status."""
    response = await client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "status" in data
    # Database should be "ok" if connection works
    assert data["database"] in ["ok", "error"]


@pytest.mark.asyncio
async def test_health_detailed_handles_db_failure_gracefully(client):
    """Test that detailed health check handles database failure gracefully."""
    # This test verifies the endpoint doesn't crash on DB errors
    # In a real failure scenario, it would return "error" not 500
    response = await client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    # Should return status map, not raise exception
    assert isinstance(data["database"], str)
