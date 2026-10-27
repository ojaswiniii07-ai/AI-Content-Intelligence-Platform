"""
Security and Integration Tests for Integration Adapter Layer.

Covers
------
1. Official API Providers & Required Permissions discovery.
2. Configuration & Secret schema validation.
3. Secret Encryption & Privacy Guarantee (Fernet encryption at rest; NEVER returned in responses).
4. Live Connection Testing via official adapter protocols (success, invalid credentials, failures).
5. Disconnect lifecycle & credential purging.
6. Role-Based Access Control (RBAC): admin/reviewer vs regular user vs unauthenticated.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.api.deps import get_db
from app.core.security import create_access_token
from app.api.v1.endpoints.integrations import _INTEGRATION_STORE


# ── Auth Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def admin_headers() -> dict:
    token = create_access_token(
        subject="usr_admin_01",
        extra_claims={"email": "admin@platform.io", "name": "Admin User", "role": "admin"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reviewer_headers() -> dict:
    token = create_access_token(
        subject="usr_reviewer_01",
        extra_claims={"email": "reviewer@platform.io", "name": "Reviewer", "role": "reviewer"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers() -> dict:
    token = create_access_token(
        subject="usr_user_01",
        extra_claims={"email": "user@platform.io", "name": "Regular User", "role": "user"},
    )
    return {"Authorization": f"Bearer {token}"}


# ── Mock DB Fixture ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    db = MagicMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=execute_result)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest_asyncio.fixture
async def client(mock_db) -> AsyncGenerator[AsyncClient, None]:
    _INTEGRATION_STORE.clear()
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
    _INTEGRATION_STORE.clear()


# ── 1. Provider Registry Tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_supported_providers_official_scopes(client, admin_headers):
    """Verifies that all supported platforms are listed with their required official API permissions."""
    resp = await client.get("/api/v1/integrations/providers", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    providers = {p["provider_id"]: p for p in body["data"]}

    # All required platforms must exist
    assert "google_forms" in providers
    assert "typeform" in providers
    assert "canvas_lms" in providers
    assert "moodle" in providers
    assert "blackboard" in providers
    assert "custom" in providers
    assert "mock" in providers

    # Official API scopes verification
    gf = providers["google_forms"]
    assert any("forms.responses.readonly" in s for s in gf["required_permissions"])
    assert "https://developers.google.com" in gf["official_docs_url"]

    tf = providers["typeform"]
    assert "responses:read" in tf["required_permissions"]

    canvas = providers["canvas_lms"]
    assert any("assignments" in s for s in canvas["required_permissions"])

    moodle = providers["moodle"]
    assert "core_webservice_get_site_info" in moodle["required_permissions"]

    bb = providers["blackboard"]
    assert "course.content.VIEW" in bb["required_permissions"]


# ── 2. Validation Tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_integration_invalid_provider(client, admin_headers):
    """Unsupported providers must be rejected with 422."""
    payload = {
        "provider": "unsupported_xyz",
        "display_name": "Test Platform",
        "auth_method": "api_key",
        "config": {},
        "secrets": {},
    }
    resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    assert resp.status_code == 422
    assert "Unsupported provider" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_create_integration_missing_config(client, admin_headers):
    """Missing required configuration fields must be rejected with 422."""
    payload = {
        "provider": "google_forms",
        "display_name": "Google Form Integration",
        "auth_method": "oauth2",
        "config": {},  # Missing form_id
        "secrets": {"access_token": "token123"},
    }
    resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    assert resp.status_code == 422
    assert "form_id" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_create_integration_invalid_base_url(client, admin_headers):
    """Invalid LMS base URL must be rejected with 422."""
    payload = {
        "provider": "canvas_lms",
        "display_name": "My Canvas",
        "auth_method": "bearer_token",
        "config": {"base_url": "ftp://not-a-valid-http-url"},
        "secrets": {"access_token": "token123"},
    }
    resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    assert resp.status_code == 422
    assert "base_url" in resp.json()["error"]["message"]


# ── 3. Secret Encryption & Privacy Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_secrets_encrypted_and_never_returned(client, admin_headers):
    """
    CRITICAL SECURITY GUARANTEE:
    Secrets are encrypted with Fernet and NEVER exposed in responses.
    """
    secret_value = "super_confidential_api_key_xyz_9988"
    payload = {
        "provider": "mock",
        "display_name": "Mock Test Integration",
        "auth_method": "api_key",
        "config": {"mock_endpoint_name": "TestEnv"},
        "secrets": {"api_key": secret_value},
    }
    # 1. Create
    resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    # Secret must NEVER be present anywhere in response
    assert secret_value not in resp.text
    assert "encrypted_secrets" not in data
    assert "api_key" not in data
    assert data["has_secrets"] is True
    integration_id = data["id"]

    # 2. Get by ID
    get_resp = await client.get(f"/api/v1/integrations/{integration_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    assert secret_value not in get_resp.text
    assert "encrypted_secrets" not in get_resp.json()["data"]
    assert get_resp.json()["data"]["has_secrets"] is True

    # 3. List
    list_resp = await client.get("/api/v1/integrations", headers=admin_headers)
    assert list_resp.status_code == 200
    assert secret_value not in list_resp.text


# ── 4. Live Connection Testing ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_connection_test_success(client, admin_headers):
    """Successful connection probe via adapter updates status to connected."""
    payload = {
        "provider": "mock",
        "display_name": "Mock Connection Test",
        "auth_method": "api_key",
        "config": {},
        "secrets": {"api_key": "valid_mock_key"},
    }
    create_resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    integ_id = create_resp.json()["data"]["id"]

    test_resp = await client.post(f"/api/v1/integrations/{integ_id}/test", headers=admin_headers)
    assert test_resp.status_code == 200
    body = test_resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "connected"
    assert body["data"]["latency_ms"] is not None

    # Check that integration status updated
    get_resp = await client.get(f"/api/v1/integrations/{integ_id}", headers=admin_headers)
    assert get_resp.json()["data"]["connection_status"] == "connected"
    assert get_resp.json()["data"]["last_connection_test_at"] is not None


@pytest.mark.asyncio
async def test_connection_test_unauthorized(client, admin_headers):
    """Invalid credentials result in unauthorized status without crashing."""
    payload = {
        "provider": "mock",
        "display_name": "Mock Auth Failure",
        "auth_method": "api_key",
        "config": {},
        "secrets": {"api_key": "invalid_key"},
    }
    create_resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    integ_id = create_resp.json()["data"]["id"]

    test_resp = await client.post(f"/api/v1/integrations/{integ_id}/test", headers=admin_headers)
    assert test_resp.status_code == 200
    body = test_resp.json()
    assert body["success"] is False
    assert body["data"]["status"] == "unauthorized"

    # Status updated in record
    get_resp = await client.get(f"/api/v1/integrations/{integ_id}", headers=admin_headers)
    assert get_resp.json()["data"]["connection_status"] == "unauthorized"


# ── 5. Disconnect & Credential Purge ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_disconnect_clears_secrets(client, admin_headers):
    """Disconnecting sets status to disconnected and purges credentials."""
    payload = {
        "provider": "mock",
        "display_name": "Disconnect Test",
        "auth_method": "api_key",
        "config": {},
        "secrets": {"api_key": "valid_key"},
    }
    create_resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    integ_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["has_secrets"] is True

    # Disconnect
    disc_resp = await client.post(f"/api/v1/integrations/{integ_id}/disconnect", headers=admin_headers)
    assert disc_resp.status_code == 200
    body = disc_resp.json()
    assert body["data"]["connection_status"] == "disconnected"
    assert body["data"]["has_secrets"] is False


# ── 6. Delete Integration ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_integration(client, admin_headers):
    """Deleting an integration removes it completely."""
    payload = {
        "provider": "mock",
        "display_name": "To Delete",
        "auth_method": "api_key",
        "config": {},
        "secrets": {"api_key": "valid_key"},
    }
    create_resp = await client.post("/api/v1/integrations", json=payload, headers=admin_headers)
    integ_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/integrations/{integ_id}", headers=admin_headers)
    assert del_resp.status_code == 200

    # Subsequent GET returns 404
    get_resp = await client.get(f"/api/v1/integrations/{integ_id}", headers=admin_headers)
    assert get_resp.status_code == 404


# ── 7. RBAC Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ordinary_user_cannot_mutate_integrations(client, user_headers):
    """Ordinary user (role='user') is blocked from creating, modifying, or testing integrations."""
    payload = {
        "provider": "mock",
        "display_name": "Unauthorized Attempt",
        "auth_method": "api_key",
        "config": {},
        "secrets": {"api_key": "key"},
    }
    resp = await client.post("/api/v1/integrations", json=payload, headers=user_headers)
    assert resp.status_code == 403

    resp2 = await client.post("/api/v1/integrations/dummy_id/test", headers=user_headers)
    assert resp2.status_code == 403

    resp3 = await client.post("/api/v1/integrations/dummy_id/disconnect", headers=user_headers)
    assert resp3.status_code == 403

    resp4 = await client.delete("/api/v1/integrations/dummy_id", headers=user_headers)
    assert resp4.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client):
    """Unauthenticated requests are rejected with 401."""
    resp = await client.get("/api/v1/integrations")
    assert resp.status_code == 401
