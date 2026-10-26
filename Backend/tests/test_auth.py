import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_current_user_unauthorized_without_token(client: AsyncClient):
    """Asserts that calling /api/v1/auth/me without an Authorization header returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_current_user_authorized_with_token(client: AsyncClient, auth_headers: dict):
    """Asserts that calling /api/v1/auth/me with a valid Bearer token returns 200 and user data."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "ojaswini@org.com"
    assert data["data"]["full_name"] == "Ojaswini"
    assert data["data"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_success_and_token_issue(client: AsyncClient):
    """Asserts that valid login credentials return a valid JWT token."""
    login_payload = {
        "email": "ojaswini@org.com",
        "password": "admin",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ojaswini@org.com"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Asserts that wrong credentials return 401."""
    login_payload = {
        "email": "ojaswini@org.com",
        "password": "completely_wrong_password",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
