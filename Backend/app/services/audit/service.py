from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.schemas.audit import AuditVerificationResponse


def compute_sha256_hash(
    event_id: str,
    timestamp_iso: str,
    event_type: str,
    actor_id: str,
    target_id: str,
    prev_hash: Optional[str],
    uncertainty_status: str,
) -> str:
    """Computes tamper-evident SHA-256 hash linked to previous block."""
    raw = f"{event_id}|{timestamp_iso}|{event_type}|{actor_id}|{target_id}|{prev_hash or 'GENESIS'}|{uncertainty_status}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sanitize_audit_description(description: str, max_chars: int = 180) -> str:
    """
    Minimizes sensitive content in audit log descriptions.
    Truncates full text bodies while keeping operational identifiers.
    """
    if not description:
        return ""
    clean = " ".join(description.split())
    if len(clean) > max_chars:
        return clean[:max_chars] + "… [content minimized for audit privacy]"
    return clean


async def append_audit_event(
    db: AsyncSession,
    event_type: str,
    target_type: str,
    target_id: str,
    description: str,
    actor_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    decision_rationale: Optional[str] = None,
    model_version: Optional[str] = None,
    uncertainty_status: str = "supported",
    rubric_version: Optional[int] = None,
    result_version: Optional[str] = "v1",
    evidence_references: Optional[List[Dict[str, Any]]] = None,
    raw_metadata: Optional[Dict[str, Any]] = None,
    client_ip: Optional[str] = None,
) -> AuditEvent:
    """
    Appends an immutable cryptographically chained audit event to the ledger.
    Ensures provider confidence disclaimer is included and sensitive text is minimized.
    """
    now = datetime.now(timezone.utc)
    event_id = f"evt_{uuid.uuid4().hex[:8]}"

    # Query latest event hash for chaining
    latest_res = await db.execute(
        sa.select(AuditEvent.sha256_hash).order_by(AuditEvent.created_at.desc()).limit(1)
    )
    prev_hash = latest_res.scalar_one_or_none()

    # Calculate SHA-256 hash
    sha = compute_sha256_hash(
        event_id=event_id,
        timestamp_iso=now.isoformat(),
        event_type=event_type,
        actor_id=str(actor_id or "system"),
        target_id=str(target_id),
        prev_hash=prev_hash,
        uncertainty_status=uncertainty_status,
    )

    metadata_payload = dict(raw_metadata or {})
    # Mandatory disclaimer: Never call arbitrary detector scores calibrated probabilities
    if "score" in metadata_payload or "ai_score" in metadata_payload or "confidence" in metadata_payload:
        metadata_payload["confidence_disclaimer"] = (
            "Detector scores and confidence indicators reflect raw provider heuristics and "
            "must NOT be construed as calibrated mathematical probabilities of AI involvement."
        )

    clean_desc = sanitize_audit_description(description)

    event = AuditEvent(
        id=event_id,
        workspace_id=workspace_id,
        actor_id=actor_id,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        description=clean_desc,
        decision_rationale=decision_rationale,
        model_version=model_version,
        uncertainty_status=uncertainty_status,
        rubric_version=rubric_version,
        result_version=result_version,
        evidence_references=evidence_references,
        raw_metadata=metadata_payload,
        sha256_hash=sha,
        prev_hash=prev_hash,
        tamper_status="Verified",
        client_ip=client_ip,
        created_at=now,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def verify_ledger_integrity(db: AsyncSession) -> AuditVerificationResponse:
    """
    Validates cryptographic hash chain across all audit events in chronological order.
    Returns status and identifies any tampered blocks.
    """
    events_res = await db.execute(
        sa.select(AuditEvent).order_by(AuditEvent.created_at.asc())
    )
    events = events_res.scalars().all()

    if not events:
        return AuditVerificationResponse(
            chain_verified=True,
            total_events=0,
            status="Empty ledger",
            tampered_event_ids=[],
        )

    tampered_ids: List[str] = []
    expected_prev = None

    for evt in events:
        # Check chaining
        if evt.prev_hash != expected_prev:
            tampered_ids.append(evt.id)

        # Recompute hash
        recomputed = compute_sha256_hash(
            event_id=evt.id,
            timestamp_iso=evt.created_at.isoformat() if evt.created_at else "",
            event_type=evt.event_type,
            actor_id=str(evt.actor_id or "system"),
            target_id=evt.target_id,
            prev_hash=evt.prev_hash,
            uncertainty_status=evt.uncertainty_status or "supported",
        )
        if recomputed != evt.sha256_hash:
            tampered_ids.append(evt.id)

        expected_prev = evt.sha256_hash

    is_valid = len(tampered_ids) == 0
    return AuditVerificationResponse(
        chain_verified=is_valid,
        total_events=len(events),
        root_hash=events[0].sha256_hash if events else None,
        last_hash=events[-1].sha256_hash if events else None,
        status="Verified (Immutable hash chain intact)" if is_valid else "Tamper Detected",
        tampered_event_ids=list(set(tampered_ids)),
    )
