import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Asserts that /api/v1/health returns 200 OK and expected structure."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_probe_dynamic_check(client: AsyncClient):
    """
    Asserts that /api/v1/ready actively executes a database query.
    If the database is not running, it must return 503 Service Unavailable and status degraded,
    never falsely reporting connected!
    """
    response = await client.get("/api/v1/ready")
    data = response.json()
    assert "database" in data
    assert "status" in data
    assert "timestamp" in data

    if data["database"]["connected"] is True:
        assert response.status_code == 200
        assert data["status"] == "ready"
        assert data["database"]["status"] == "operational"
    else:
        # If DB is not active locally, status code MUST be 503 and degraded
        assert response.status_code == 503
        assert data["status"] == "degraded"
        assert data["database"]["status"] == "unavailable"
        assert data["database"]["connected"] is False
