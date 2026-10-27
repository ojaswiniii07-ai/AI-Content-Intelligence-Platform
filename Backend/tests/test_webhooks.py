"""
Security and Integrity Tests for Webhooks Engine.

Covers
------
1. Webhook Endpoint Registration & Single-use Signing Secret Display.
2. HMAC-SHA256 Signature Generation & Header Verification.
3. Replay Protection (tolerance window check).
4. Delivery Logging & Audit Trail (endpoint counters, status, timestamps).
5. Data Minimization & Privacy Protection (suppression of full media & binary payloads).
6. RBAC & Unauthorized Access Prevention.
"""
from __future__ import annotations

import json
import sys
import time
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
from app.core.crypto import sign_webhook_payload
from app.core.security import create_access_token
from app.api.v1.endpoints.webhooks import _ENDPOINT_STORE, _DELIVERY_STORE
from app.services.webhooks.dispatcher import build_webhook_payload


# ── Auth Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def admin_headers() -> dict:
    token = create_access_token(
        subject="usr_admin_01",
        extra_claims={"email": "admin@platform.io", "name": "Admin User", "role": "admin"},
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
    _ENDPOINT_STORE.clear()
    _DELIVERY_STORE.clear()
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
    _ENDPOINT_STORE.clear()
    _DELIVERY_STORE.clear()


# ── 1. Endpoint Registration & Secret Handling ───────────────────────────────

@pytest.mark.asyncio
async def test_register_webhook_endpoint_shows_secret_once(client, admin_headers):
    """
    Signing secret is returned ONCE during registration and NEVER again in subsequent queries.
    """
    payload = {
        "integration_id": "integ_001",
        "target_url": "https://mock.example.com/webhook",
        "display_name": "LMS Sync Webhook",
        "event_types": ["job.completed", "job.failed"],
        "include_full_payload": False,
    }
    resp = await client.post("/api/v1/webhooks/endpoints", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    # Secret is present in creation response
    assert "signing_secret" in data
    signing_secret = data["signing_secret"]
    assert len(signing_secret) >= 32
    assert "sha256" in data["verification_instructions"]
    endpoint_id = data["id"]

    # Subsequent GET must NEVER expose the secret
    get_resp = await client.get(f"/api/v1/webhooks/endpoints/{endpoint_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    get_data = get_resp.json()["data"]
    assert "signing_secret" not in get_data
    assert "encrypted_signing_secret" not in get_data
    assert signing_secret not in get_resp.text

    # List endpoints must NEVER expose secrets
    list_resp = await client.get("/api/v1/webhooks/endpoints", headers=admin_headers)
    assert list_resp.status_code == 200
    assert signing_secret not in list_resp.text


@pytest.mark.asyncio
async def test_register_invalid_url_rejected(client, admin_headers):
    """Invalid non-HTTP target URLs are rejected with 422."""
    payload = {
        "integration_id": "integ_001",
        "target_url": "javascript:alert(1)",
        "display_name": "Bad URL",
    }
    resp = await client.post("/api/v1/webhooks/endpoints", json=payload, headers=admin_headers)
    assert resp.status_code == 422


# ── 2. Test Ping & Delivery History ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_test_ping_and_delivery_logging(client, admin_headers):
    """Dispatching a test ping creates a logged WebhookDelivery record."""
    create_payload = {
        "integration_id": "integ_001",
        "target_url": "https://mock.example.com/webhook-listener",
        "display_name": "Listener Test",
    }
    reg_resp = await client.post("/api/v1/webhooks/endpoints", json=create_payload, headers=admin_headers)
    endpoint_id = reg_resp.json()["data"]["id"]

    # Dispatch test ping
    test_resp = await client.post(f"/api/v1/webhooks/endpoints/{endpoint_id}/test", headers=admin_headers)
    assert test_resp.status_code == 200
    delivery_data = test_resp.json()["data"]

    assert delivery_data["status"] == "delivered"
    assert delivery_data["event_type"] == "test.ping"
    assert delivery_data["signature_header"] is not None
    assert delivery_data["signature_header"].startswith("sha256=")
    assert delivery_data["event_timestamp"] > 0

    # Query delivery log
    log_resp = await client.get(f"/api/v1/webhooks/endpoints/{endpoint_id}/deliveries", headers=admin_headers)
    assert log_resp.status_code == 200
    log_items = log_resp.json()["data"]
    assert len(log_items) >= 1
    assert log_items[0]["status"] == "delivered"


# ── 3. HMAC Signature & Replay Protection Verification ───────────────────────

@pytest.mark.asyncio
async def test_signature_verification_success(client, admin_headers):
    """Valid HMAC-SHA256 signature and fresh timestamp pass verification."""
    secret = "f4c9a81e7d2358bc103759a20468e2f01234567890abcdef1234567890abcdef"
    payload_str = json.dumps({"event_id": "evt-123", "status": "completed"}, separators=(",", ":"))
    sig = sign_webhook_payload(secret, payload_str.encode("utf-8"))
    current_ts = str(int(time.time()))

    verify_req = {
        "signing_secret": secret,
        "payload": payload_str,
        "signature_header": sig,
        "timestamp_header": current_ts,
        "tolerance_seconds": 300,
    }
    resp = await client.post("/api/v1/webhooks/verify", json=verify_req, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["valid"] is True
    assert body["data"]["reason"] == "Valid"


@pytest.mark.asyncio
async def test_tampered_payload_rejected(client, admin_headers):
    """Tampered payload fails HMAC signature verification."""
    secret = "f4c9a81e7d2358bc103759a20468e2f01234567890abcdef1234567890abcdef"
    original_payload = '{"event_id": "evt-123", "score": 90}'
    sig = sign_webhook_payload(secret, original_payload.encode("utf-8"))

    tampered_payload = '{"event_id": "evt-123", "score": 100}'

    verify_req = {
        "signing_secret": secret,
        "payload": tampered_payload,
        "signature_header": sig,
        "timestamp_header": str(int(time.time())),
        "tolerance_seconds": 300,
    }
    resp = await client.post("/api/v1/webhooks/verify", json=verify_req, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["valid"] is False
    assert "mismatch" in resp.json()["data"]["reason"].lower()


@pytest.mark.asyncio
async def test_replay_attack_rejected(client, admin_headers):
    """Timestamp older than tolerance window is rejected to defend against replay attacks."""
    secret = "f4c9a81e7d2358bc103759a20468e2f01234567890abcdef1234567890abcdef"
    payload_str = '{"event_id": "evt-replayed", "status": "done"}'
    sig = sign_webhook_payload(secret, payload_str.encode("utf-8"))

    # 10 minutes ago (600s > 300s tolerance)
    old_timestamp = str(int(time.time()) - 600)

    verify_req = {
        "signing_secret": secret,
        "payload": payload_str,
        "signature_header": sig,
        "timestamp_header": old_timestamp,
        "tolerance_seconds": 300,
    }
    resp = await client.post("/api/v1/webhooks/verify", json=verify_req, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["valid"] is False
    assert "tolerance" in resp.json()["data"]["reason"].lower()


# ── 4. Privacy Protection & Payload Minimization ──────────────────────────────

def test_payload_builder_privacy_protection():
    """Default webhook payloads exclude sensitive full text and raw media binaries."""
    full_data = {
        "essay_full_text": "Sensitive student confidential essay content...",
        "media_binary": b"0101010101010101",
        "secrets": {"api_key": "leak_me_not"},
        "clean_metric": 95.5,
    }

    # Default: include_full_payload=False
    summary_payload = build_webhook_payload(
        event_type="job.completed",
        submission_id="sub_99",
        status="completed",
        summary_data={"ai_score": 12.0},
        full_data=full_data,
        include_full_payload=False,
    )
    assert "details" not in summary_payload
    assert summary_payload["summary"]["ai_score"] == 12.0

    # With include_full_payload=True: binary and secret keys stripped
    full_payload = build_webhook_payload(
        event_type="job.completed",
        submission_id="sub_99",
        status="completed",
        summary_data={"ai_score": 12.0},
        full_data=full_data,
        include_full_payload=True,
    )
    assert "details" in full_payload
    assert "media_binary" not in full_payload["details"]
    assert "secrets" not in full_payload["details"]
    assert full_payload["details"]["clean_metric"] == 95.5


# ── 5. RBAC Enforcement ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ordinary_user_cannot_register_webhooks(client, user_headers):
    """Ordinary user is blocked from managing webhook endpoints (403 Forbidden)."""
    payload = {
        "integration_id": "integ_001",
        "target_url": "https://listener.example.com",
        "display_name": "Unauthorized Webhook",
    }
    resp = await client.post("/api/v1/webhooks/endpoints", json=payload, headers=user_headers)
    assert resp.status_code == 403

    resp2 = await client.post("/api/v1/webhooks/endpoints/ep_01/test", headers=user_headers)
    assert resp2.status_code == 403

    resp3 = await client.delete("/api/v1/webhooks/endpoints/ep_01", headers=user_headers)
    assert resp3.status_code == 403
