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
