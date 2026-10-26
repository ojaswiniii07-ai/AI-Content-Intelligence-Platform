import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_not_found_endpoint(client: AsyncClient):
    """Asserts that requests to non-existent endpoints return structured 404 response."""
    response = await client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"


@pytest.mark.asyncio
async def test_validation_error_handling(client: AsyncClient):
    """Asserts that invalid request payloads trigger 422 with structured field details."""
    invalid_login = {
        "email": "not-an-email",  # fails email format validation
        # missing password field
    }
    response = await client.post("/api/v1/auth/login", json=invalid_login)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "validation_errors" in data["error"]["details"]
    assert len(data["error"]["details"]["validation_errors"]) > 0


@pytest.mark.asyncio
async def test_simulator_out_of_bounds_validation(client: AsyncClient, auth_headers: dict):
    """Asserts that threshold > 1.0 fails validation."""
    invalid_sim = {
        "threshold": 1.5,  # must be <= 1.0
        "model_version": "v2.4",
        "dataset": "edu",
    }
    response = await client.post("/api/v1/analysis/simulator", json=invalid_sim, headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
