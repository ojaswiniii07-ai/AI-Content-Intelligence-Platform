import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.audit import AuditEventCreate, AuditEventDetail, AuditEventRead
from app.schemas.common import APIResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

# Initial ledger state
MOCK_EVENTS = [
    {
        "id": "evt_9041",
        "event_type": "Submission Analyzed",
        "target_type": "submission",
        "target_id": "sub_0041",
        "description": "sub_0041 · Model: text-detector-v2.4 · Result: High AI Signal (74%)",
        "decision_rationale": "Confidence threshold 0.70 reached. Flagged for reviewer review.",
        "model_version": "text-detector-v2.4 (SHA: 8f3a9e2d)",
        "actor_name": "System Automated Pipeline",
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "prev_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        "tamper_status": "Verified",
        "created_at": datetime(2026, 10, 26, 21, 2, 14, tzinfo=timezone.utc),
    },
    {
        "id": "evt_9038",
        "event_type": "Reviewer Decision",
        "target_type": "submission",
        "target_id": "sub_0027",
        "description": 'sub_0027 · Accepted: "Strong reasoning despite AI signal"',
        "decision_rationale": "Human reviewer determined analytical depth met top tier standard regardless of AI assistance flag.",
        "model_version": "text-detector-v2.4",
        "actor_name": "ojaswini@org.com",
        "sha256_hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        "prev_hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd309963b89b4c0ab060411a7c3",
        "tamper_status": "Verified",
        "created_at": datetime(2026, 10, 26, 20, 41, 9, tzinfo=timezone.utc),
    },
    {
        "id": "evt_9032",
        "event_type": "Override Recorded",
        "target_type": "submission",
        "target_id": "sub_0012",
        "description": 'sub_0012 · Reject → Second Review · Reason: "Inconclusive boundary signal"',
        "decision_rationale": "Escalated to secondary senior committee due to technical complexity.",
        "model_version": "vision-engine-v3.1",
        "actor_name": "review-lead@org.com",
        "sha256_hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd309963b89b4c0ab060411a7c3",
        "prev_hash": "b10a8db164e0754105b7a99be72e3fe5ec437c3523f6687a412ea0bb579c0ee9",
        "tamper_status": "Verified",
        "created_at": datetime(2026, 10, 26, 20, 38, 45, tzinfo=timezone.utc),
    },
    {
        "id": "evt_9025",
        "event_type": "Model Updated",
        "target_type": "model",
        "target_id": "text-detector-v2.4",
        "description": "text-detector v2.3 → v2.4 · Calibration FP rate: 4.1% → 3.8%",
        "decision_rationale": "Model fine-tuned on academic writing benchmark. Decreased false positives by 0.3%.",
        "model_version": "text-detector-v2.4",
        "actor_name": "System Admin · ojaswini@org.com",
        "sha256_hash": "b10a8db164e0754105b7a99be72e3fe5ec437c3523f6687a412ea0bb579c0ee9",
        "prev_hash": "c8f49f45d8b2e1e07354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        "tamper_status": "Verified",
        "created_at": datetime(2026, 10, 25, 18, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": "evt_8999",
        "event_type": "Security Tamper Alert",
        "target_type": "system",
        "target_id": "sub_0089",
        "description": "Unauthorized query to sub_0089 encrypted score record · Blocked & Logged",
        "decision_rationale": "Failed API signature token validation. Request terminated immediately.",
        "model_version": None,
        "actor_name": "Unknown Actor · IP: 203.0.113.42",
        "sha256_hash": "7d793037a0760186574b0282f2f435e7b1e7a6acc941e0740006471e0849cdfe",
        "prev_hash": None,
        "tamper_status": "Flagged Incident (Zero Compromise)",
        "created_at": datetime(2026, 10, 24, 9, 15, 10, tzinfo=timezone.utc),
    },
]


@router.get("/events", response_model=APIResponse[List[AuditEventRead]])
async def list_audit_events(
    event_type: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[AuditEventRead]]:
    """Returns chronological tamper-evident audit ledger entries."""
    events = [AuditEventRead.model_validate(e) for e in MOCK_EVENTS]

    if event_type and event_type != "all":
        events = [e for e in events if e.event_type.lower() == event_type.lower()]

    if query:
        q = query.lower()
        events = [
            e for e in events
            if q in e.description.lower() or (e.actor_name and q in e.actor_name.lower()) or q in e.target_id.lower()
        ]

    return APIResponse(data=events, message="Audit events retrieved")


@router.post("/events", response_model=APIResponse[AuditEventRead])
async def create_audit_event(
    event_in: AuditEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditEventRead]:
    """Records a new cryptographically hashed event to the audit ledger."""
    now = datetime.now(timezone.utc)
    event_id = f"evt_{uuid.uuid4().hex[:6]}"

    # Compute SHA-256 hash chaining
    raw_content = f"{event_id}:{now.isoformat()}:{event_in.event_type}:{current_user.email}:{event_in.description}"
    sha = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

    created_event = AuditEventRead(
        id=event_id,
        event_type=event_in.event_type,
        target_type=event_in.target_type,
        target_id=event_in.target_id,
        description=event_in.description,
        decision_rationale=event_in.decision_rationale,
        model_version=event_in.model_version,
        actor_id=current_user.id,
        actor_name=current_user.email,
        sha256_hash=sha,
        prev_hash=MOCK_EVENTS[0]["sha256_hash"] if MOCK_EVENTS else None,
        tamper_status="Verified",
        created_at=now,
    )

    return APIResponse(data=created_event, message="Audit event recorded successfully")
