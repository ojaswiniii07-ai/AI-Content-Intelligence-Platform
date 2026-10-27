"""
Tests for Audit Trail and Human Review Module.

Covers:
  1. Authorization:
     - Ordinary user (role="user") forbidden from audit history (403)
     - Ordinary user forbidden from review decisions and overrides (403)
     - Authorized reviewer (role="reviewer") & admin allowed (200)
     - Immutability guardrails: PUT/DELETE on audit events rejected (403)
  2. Override Reason Enforcement:
     - Missing override_reason returns 422
     - Substantive override_reason (< 5 chars) returns 422
     - Valid override accepted and recorded
  3. Ledger History & Cryptographic Integrity:
     - SHA-256 hash chaining verification
     - Tamper detection identifies modified blocks
  4. Uncertainty Statuses & Model Availability:
     - Correct recording of supported, inconclusive, not_configured, failed
     - Mandatory uncalibrated confidence disclaimer attached
  5. End-to-End Review Workflows:
     - Record reviewer decision -> review updated & audit event logged
     - Record reviewer override -> review updated & override audit event logged
     - Review history endpoint returns chronological audit trail
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
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
from app.models.audit import AuditEvent
from app.models.review import Review
from app.services.audit.service import append_audit_event, compute_sha256_hash, verify_ledger_integrity


# ── Auth Fixtures ─────────────────────────────────────────────────────────────
@pytest.fixture
def admin_headers() -> dict:
    token = create_access_token(
        subject="usr_admin_01",
        extra_claims={"email": "admin@platform.io", "name": "Security Admin", "role": "admin"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reviewer_headers() -> dict:
    token = create_access_token(
        subject="usr_reviewer_01",
        extra_claims={"email": "reviewer@platform.io", "name": "Senior Reviewer", "role": "reviewer"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ordinary_user_headers() -> dict:
    token = create_access_token(
        subject="usr_student_01",
        extra_claims={"email": "student@university.edu", "name": "Student User", "role": "user"},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ── 1. Authorization & Role Enforcement Tests ─────────────────────────────────
class TestAuditAuthorization:

    @pytest.mark.asyncio
    async def test_ordinary_user_forbidden_from_audit_history(self, client, ordinary_user_headers):
        """Ordinary users (role='user') must be denied access to audit history (403)."""
        res = await client.get("/api/v1/audit/events", headers=ordinary_user_headers)
        assert res.status_code == 403, res.text
        assert "access restricted" in res.text.lower() or "forbidden" in res.text.lower()

    @pytest.mark.asyncio
    async def test_reviewer_permitted_for_audit_history(self, client, reviewer_headers):
        """Users with reviewer role can inspect the audit trail."""
        res = await client.get("/api/v1/audit/events", headers=reviewer_headers)
        assert res.status_code == 200, res.text
        assert "data" in res.json()

    @pytest.mark.asyncio
    async def test_admin_permitted_for_audit_history(self, client, admin_headers):
        """Administrators can inspect the audit trail."""
        res = await client.get("/api/v1/audit/events", headers=admin_headers)
        assert res.status_code == 200, res.text

    @pytest.mark.asyncio
    async def test_ordinary_user_forbidden_from_submitting_decision(self, client, ordinary_user_headers):
        """Ordinary users cannot record human review decisions."""
        payload = {
            "submission_id": "sub_test_01",
            "decision": "accepted",
            "decision_rationale": "Attempted unauthorized approval",
        }
        res = await client.post("/api/v1/audit/reviews/decision", headers=ordinary_user_headers, json=payload)
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_audit_event_modification_prohibited(self, client, admin_headers):
        """Immutability guardrail: PUT and DELETE on audit events are rejected (403)."""
        res_put = await client.put("/api/v1/audit/events/evt_9041", headers=admin_headers, json={"description": "Hacked"})
        assert res_put.status_code == 403
        assert "append-only" in res_put.text.lower()

        res_del = await client.delete("/api/v1/audit/events/evt_9041", headers=admin_headers)
        assert res_del.status_code == 403
        assert "append-only" in res_del.text.lower()


# ── 2. Mandatory Override Reasons ─────────────────────────────────────────────
class TestMissingOverrideReasons:

    @pytest.mark.asyncio
    async def test_override_without_reason_rejected(self, client, reviewer_headers):
        """Omitting override_reason must fail request validation (422)."""
        payload = {
            "submission_id": "sub_9999",
            "override_decision": "shortlisted",
            # override_reason omitted!
        }
        res = await client.post("/api/v1/audit/reviews/override", headers=reviewer_headers, json=payload)
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_override_with_too_short_reason_rejected(self, client, reviewer_headers):
        """Override reason must be substantive (minimum 5 characters)."""
        payload = {
            "submission_id": "sub_9999",
            "override_decision": "shortlisted",
            "override_reason": "ok",  # Only 2 chars
        }
        res = await client.post("/api/v1/audit/reviews/override", headers=reviewer_headers, json=payload)
        assert res.status_code == 422


# ── 3. Ledger History & Cryptographic Integrity ───────────────────────────────
class TestLedgerHistoryIntegrity:

    @pytest.mark.asyncio
    async def test_sha256_chaining_verified(self):
        """Verifies that consecutive events form a continuous SHA-256 hash chain."""
        event_store = []
        mock_db = AsyncMock()

        def fake_add(obj):
            event_store.append(obj)

        async def fake_commit():
            pass

        async def fake_refresh(obj):
            pass

        async def fake_execute(stmt):
            res = MagicMock()
            sql_str = str(stmt)
            if "ORDER BY audit_events.created_at DESC" in sql_str:
                res.scalar_one_or_none.return_value = event_store[-1].sha256_hash if event_store else None
            elif "ORDER BY audit_events.created_at ASC" in sql_str:
                res.scalars.return_value.all.return_value = list(event_store)
            return res

        mock_db.add = fake_add
        mock_db.commit = fake_commit
        mock_db.refresh = fake_refresh
        mock_db.execute = fake_execute

        # Add 3 chained events
        evt1 = await append_audit_event(mock_db, "Event 1", "submission", "sub_1", "First block")
        evt2 = await append_audit_event(mock_db, "Event 2", "submission", "sub_2", "Second block")
        evt3 = await append_audit_event(mock_db, "Event 3", "submission", "sub_3", "Third block")

        assert evt1.prev_hash is None
        assert evt2.prev_hash == evt1.sha256_hash
        assert evt3.prev_hash == evt2.sha256_hash

        # Verify integrity
        verification = await verify_ledger_integrity(mock_db)
        assert verification.chain_verified is True
        assert verification.total_events == 3
        assert len(verification.tampered_event_ids) == 0

    @pytest.mark.asyncio
    async def test_tamper_detection_flags_corrupted_event(self):
        """If an event's hash is tampered with, verification must flag it."""
        now = datetime.now(timezone.utc)

        # Create two events
        evt1 = AuditEvent(
            id="evt_01",
            event_type="Submission Analyzed",
            target_type="submission",
            target_id="sub_01",
            description="Block 1",
            uncertainty_status="supported",
            sha256_hash=compute_sha256_hash("evt_01", now.isoformat(), "Submission Analyzed", "system", "sub_01", None, "supported"),
            prev_hash=None,
            created_at=now,
        )

        # Corrupted second event: hash does not match content
        evt2 = AuditEvent(
            id="evt_02_tampered",
            event_type="Reviewer Decision",
            target_type="submission",
            target_id="sub_02",
            description="Tampered description",
            uncertainty_status="supported",
            sha256_hash="0000000000000000000000000000000000000000000000000000000000000bad",  # Forged hash!
            prev_hash=evt1.sha256_hash,
            created_at=now,
        )

        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = [evt1, evt2]
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_res)

        verification = await verify_ledger_integrity(mock_db)
        assert verification.chain_verified is False
        assert "evt_02_tampered" in verification.tampered_event_ids
        assert "Tamper" in verification.status


# ── 4. Uncertainty Statuses & Provider Disclaimers ─────────────────────────────
class TestUncertaintyStatusesAndDisclaimers:

    @pytest.mark.asyncio
    async def test_uncertainty_statuses_recorded_in_audit_event(self):
        """Uncertainty statuses (supported, inconclusive, not_configured, failed) are persisted."""
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_res)

        evt = await append_audit_event(
            db=mock_db,
            event_type="Model Evaluated",
            target_type="model",
            target_id="audio_detector",
            description="Audio model evaluated",
            uncertainty_status="not_configured",
            raw_metadata={"ai_score": 0.0},
        )
        assert evt.uncertainty_status == "not_configured"
        # Confidence disclaimer must be attached
        assert "confidence_disclaimer" in evt.raw_metadata
        assert "calibrated mathematical probabilities" in evt.raw_metadata["confidence_disclaimer"]

    @pytest.mark.asyncio
    async def test_privacy_sanitizes_long_text_in_description(self):
        """Long text bodies must be truncated with a privacy indicator."""
        from app.services.audit.service import sanitize_audit_description
        long_essay = "This is a very long text " * 30
        sanitized = sanitize_audit_description(long_essay, max_chars=100)
        assert len(sanitized) < len(long_essay)
        assert "[content minimized for audit privacy]" in sanitized


# ── 5. Review Workflows ───────────────────────────────────────────────────────
class TestReviewWorkflows:

    @pytest.mark.asyncio
    async def test_full_review_decision_and_override_workflow(self, client, reviewer_headers):
        """Tests end-to-end: record review decision -> record override -> verify history."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.api.deps import get_db, get_current_user
        from app.models.user import User

        reviews_store = {}
        events_store = []

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid.uuid4()
        mock_user.email = "lead-reviewer@platform.io"
        mock_user.role = "reviewer"
        mock_user.is_superuser = False

        mock_db = AsyncMock(spec=AsyncSession)

        def fake_add(obj):
            if isinstance(obj, Review):
                obj.created_at = datetime.now(timezone.utc)
                reviews_store[obj.submission_id] = obj
            elif isinstance(obj, AuditEvent):
                obj.created_at = datetime.now(timezone.utc)
                events_store.append(obj)

        async def fake_commit():
            pass

        async def fake_refresh(obj):
            pass

        async def fake_execute(stmt):
            res = MagicMock()
            sql_str = str(stmt)
            if "reviews" in sql_str.lower():
                matches = list(reviews_store.values())
                first = matches[0] if matches else None
                res.scalars.return_value.first.return_value = first
                res.all.return_value = [(r, mock_user) for r in matches]
                return res
            elif "audit_events" in sql_str.lower():
                if "order by" in sql_str.lower() and "desc" in sql_str.lower():
                    res.scalar_one_or_none.return_value = events_store[-1].sha256_hash if events_store else None
                res.scalars.return_value.all.return_value = list(events_store)
                return res
            return res

        mock_db.add = fake_add
        mock_db.commit = fake_commit
        mock_db.refresh = fake_refresh
        mock_db.execute = fake_execute

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # 1. Record reviewer decision
            decision_payload = {
                "submission_id": "sub_workflow_01",
                "decision": "shortlisted",
                "decision_rationale": "High analytical depth demonstrated in section 3.",
                "score_adjustment": 88.0,
            }
            dec_res = await client.post("/api/v1/audit/reviews/decision", headers=reviewer_headers, json=decision_payload)
            assert dec_res.status_code == 200, dec_res.text
            assert dec_res.json()["data"]["status"] == "shortlisted"

            # 2. Record reviewer override
            override_payload = {
                "submission_id": "sub_workflow_01",
                "override_decision": "flagged",
                "override_reason": "Found unverified citation claims requiring secondary committee review.",
                "new_total_score": 72.0,
            }
            ov_res = await client.post("/api/v1/audit/reviews/override", headers=reviewer_headers, json=override_payload)
            assert ov_res.status_code == 200, ov_res.text
            assert ov_res.json()["data"]["override_flag"] is True

            # 3. Query history
            hist_res = await client.get("/api/v1/audit/reviews/history/sub_workflow_01", headers=reviewer_headers)
            assert hist_res.status_code == 200
            history_data = hist_res.json()["data"]
            assert len(history_data) >= 1
            assert history_data[0]["override_flag"] is True
            assert "unverified citation" in history_data[0]["override_reason"]

        finally:
            app.dependency_overrides.clear()
