from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.models.audit import AuditEvent
from app.models.review import Review
from app.models.user import User
from app.schemas.audit import (
    AuditEventCreate,
    AuditEventDetail,
    AuditEventRead,
    AuditVerificationResponse,
    ReviewDecisionRequest,
    ReviewHistoryItem,
    ReviewOverrideRequest,
    UncertaintyStatus,
)
from app.schemas.common import APIResponse
from app.services.audit.service import append_audit_event, verify_ledger_integrity

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

# Initial ledger state for initial demonstration / frontend parity
MOCK_EVENTS = [
    {
        "id": "evt_9041",
        "event_type": "Submission Analyzed",
        "target_type": "submission",
        "target_id": "sub_0041",
        "description": "sub_0041 · Model: text-detector-v2.4 · Result: High AI Signal (74%)",
        "decision_rationale": "Confidence threshold 0.70 reached. Flagged for reviewer review.",
        "model_version": "text-detector-v2.4 (SHA: 8f3a9e2d)",
        "uncertainty_status": "supported",
        "rubric_version": 1,
        "result_version": "v1",
        "evidence_references": [{"reference_type": "sentence_offset", "identifier": "sent_04", "location": "120-184"}],
        "raw_metadata": {"confidence_disclaimer": "Detector scores are raw uncalibrated provider signals."},
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
        "uncertainty_status": "supported",
        "rubric_version": 1,
        "result_version": "v1",
        "evidence_references": [],
        "raw_metadata": {},
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
        "uncertainty_status": "inconclusive",
        "rubric_version": 1,
        "result_version": "v1",
        "evidence_references": [{"reference_type": "frame_reference", "identifier": "frame_018"}],
        "raw_metadata": {},
        "actor_name": "review-lead@org.com",
        "sha256_hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd309963b89b4c0ab060411a7c3",
        "prev_hash": "b10a8db164e0754105b7a99be72e3fe5ec437c3523f6687a412ea0bb579c0ee9",
        "tamper_status": "Verified",
        "created_at": datetime(2026, 10, 26, 20, 38, 45, tzinfo=timezone.utc),
    },
]


# ── 1. Audit History (Role Enforced: admin, reviewer, auditor) ────────────────
@router.get("/events", response_model=APIResponse[List[AuditEventRead]])
@router.get("/history", response_model=APIResponse[List[AuditEventRead]])
async def list_audit_events(
    event_type: Optional[str] = Query(None),
    uncertainty_status: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("admin", "reviewer", "auditor")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[AuditEventRead]]:
    """
    Returns chronological tamper-evident audit ledger entries.
    Requires reviewer, auditor, or admin role. Ordinary users cannot view audit history.
    """
    # Fetch from database
    stmt = sa.select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if event_type and event_type != "all":
        stmt = stmt.where(AuditEvent.event_type.ilike(f"%{event_type}%"))
    if uncertainty_status:
        stmt = stmt.where(AuditEvent.uncertainty_status == uncertainty_status)
    if target_id:
        stmt = stmt.where(AuditEvent.target_id == target_id)

    try:
        db_res = await db.execute(stmt)
        db_events = db_res.scalars().all()
    except Exception:
        db_events = []

    if db_events:
        events = [AuditEventRead.model_validate(e) for e in db_events]
    else:
        # Fallback to demo baseline events
        events = [AuditEventRead.model_validate(e) for e in MOCK_EVENTS]
        if event_type and event_type != "all":
            events = [e for e in events if e.event_type.lower() == event_type.lower()]
        if uncertainty_status:
            events = [e for e in events if e.uncertainty_status == uncertainty_status]
        if target_id:
            events = [e for e in events if e.target_id == target_id]

    if query:
        q = query.lower()
        events = [
            e for e in events
            if q in e.description.lower()
            or (e.actor_name and q in e.actor_name.lower())
            or q in e.target_id.lower()
        ]

    return APIResponse(data=events, message="Audit events retrieved")


@router.get("/events/{event_id}", response_model=APIResponse[AuditEventDetail])
async def get_audit_event_detail(
    event_id: str,
    current_user: User = Depends(require_roles("admin", "reviewer", "auditor")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditEventDetail]:
    """Retrieve detailed cryptographic information for a single audit event."""
    try:
        stmt = sa.select(AuditEvent).where(AuditEvent.id == event_id)
        res = await db.execute(stmt)
        event = res.scalars().first()
    except Exception:
        event = None

    if not event:
        # Check mock events
        mock_match = next((e for e in MOCK_EVENTS if e["id"] == event_id), None)
        if mock_match:
            return APIResponse(data=AuditEventDetail.model_validate(mock_match), message="Audit event retrieved")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audit event '{event_id}' not found.")

    return APIResponse(data=AuditEventDetail.model_validate(event), message="Audit event retrieved")


# ── 2. Ledger Hash Chain Verification ─────────────────────────────────────────
@router.get("/verify", response_model=APIResponse[AuditVerificationResponse])
async def verify_audit_ledger(
    current_user: User = Depends(require_roles("admin", "reviewer", "auditor")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditVerificationResponse]:
    """
    Verifies cryptographic hash chain across the append-only ledger.
    Detects any tampering or modifications to historical events.
    """
    verification = await verify_ledger_integrity(db)
    return APIResponse(data=verification, message="Ledger integrity verification completed")


# ── 3. Append-Only Guardrails (Prevent Edit / Delete) ─────────────────────────
@router.put("/events/{event_id}")
async def reject_audit_event_edit(
    event_id: str,
    current_user: User = Depends(get_current_user),
):
    """Guarantees ledger immutability: edits are strictly prohibited."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Audit ledger is append-only. Historical audit records cannot be modified.",
    )


@router.delete("/events/{event_id}")
async def reject_audit_event_deletion(
    event_id: str,
    current_user: User = Depends(get_current_user),
):
    """Guarantees ledger immutability: deletions are strictly prohibited."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Audit ledger is append-only. Deletion of audit records is strictly prohibited.",
    )


# ── 4. Human Review Decisions & Overrides ──────────────────────────────────────
@router.post(
    "/reviews/decision",
    response_model=APIResponse[Dict[str, Any]],
    summary="Record authorized human reviewer decision and append audit event",
)
async def record_reviewer_decision(
    req: ReviewDecisionRequest,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """
    Records a reviewer's decision on a submission.
    Creates or updates the review record and appends a tamper-evident audit event.
    """
    rev_res = await db.execute(
        sa.select(Review).where(Review.submission_id == req.submission_id)
    )
    review = rev_res.scalars().first()

    now = datetime.now(timezone.utc)
    review_id = review.id if review else str(uuid.uuid4())

    if review:
        review.status = req.decision
        review.decision_rationale = req.decision_rationale
        if req.score_adjustment is not None:
            review.total_score = req.score_adjustment
        if req.notes:
            review.notes = req.notes
    else:
        review = Review(
            id=review_id,
            submission_id=req.submission_id,
            reviewer_id=str(current_user.id),
            rubric_id=req.rubric_id,
            total_score=req.score_adjustment or 75.0,
            status=req.decision,
            notes=req.notes,
        )
        db.add(review)

    # Append immutable audit event
    audit_evt = await append_audit_event(
        db=db,
        event_type="Reviewer Decision",
        target_type="submission",
        target_id=req.submission_id,
        description=f"{req.submission_id} · Decision: {req.decision} · Reviewer: {current_user.email}",
        actor_id=str(current_user.id),
        decision_rationale=req.decision_rationale,
        uncertainty_status="supported",
        raw_metadata={
            "review_id": review_id,
            "decision": req.decision,
            "reviewer_email": current_user.email,
        },
    )

    return APIResponse(
        data={
            "review_id": review_id,
            "submission_id": req.submission_id,
            "status": req.decision,
            "audit_event_id": audit_evt.id,
            "recorded_at": now.isoformat(),
        },
        message=f"Reviewer decision '{req.decision}' recorded and appended to audit ledger.",
    )


@router.post(
    "/reviews/override",
    response_model=APIResponse[Dict[str, Any]],
    summary="Record manual reviewer override with mandatory rationale and append audit event",
)
async def record_reviewer_override(
    req: ReviewOverrideRequest,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """
    Applies a human reviewer override.
    Requires a non-empty override_reason (minimum 5 characters).
    Appends an immutable 'Override Recorded' event to the audit ledger.
    """
    if not req.override_reason or len(req.override_reason.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A substantive override_reason (minimum 5 characters) is mandatory for audit compliance.",
        )

    rev_res = await db.execute(
        sa.select(Review).where(Review.submission_id == req.submission_id)
    )
    review = rev_res.scalars().first()

    now = datetime.now(timezone.utc)
    review_id = review.id if review else str(uuid.uuid4())
    prev_status = review.status if review else "pending"
    prev_score = review.total_score if review else 0.0

    if review:
        review.status = req.override_decision
        review.override_flag = True
        review.override_reason = req.override_reason
        if req.new_total_score is not None:
            review.total_score = req.new_total_score
        if req.notes:
            review.notes = req.notes
    else:
        review = Review(
            id=review_id,
            submission_id=req.submission_id,
            reviewer_id=str(current_user.id),
            total_score=req.new_total_score or 75.0,
            status=req.override_decision,
            override_flag=True,
            override_reason=req.override_reason,
            notes=req.notes,
        )
        db.add(review)

    # Append immutable audit event
    audit_evt = await append_audit_event(
        db=db,
        event_type="Override Recorded",
        target_type="submission",
        target_id=req.submission_id,
        description=f"{req.submission_id} · Override: {prev_status} → {req.override_decision} · Reason: {req.override_reason}",
        actor_id=str(current_user.id),
        decision_rationale=req.override_reason,
        uncertainty_status="supported",
        raw_metadata={
            "review_id": review_id,
            "previous_status": prev_status,
            "new_status": req.override_decision,
            "previous_score": prev_score,
            "new_score": req.new_total_score or prev_score,
            "override_reason": req.override_reason,
            "reviewer_email": current_user.email,
        },
    )

    return APIResponse(
        data={
            "review_id": review_id,
            "submission_id": req.submission_id,
            "status": req.override_decision,
            "override_decision": req.override_decision,
            "override_flag": True,
            "override_reason": req.override_reason,
            "audit_event_id": audit_evt.id,
            "recorded_at": now.isoformat(),
        },
        message=f"Reviewer override recorded and appended to audit ledger.",
    )


# ── 5. Review History ─────────────────────────────────────────────────────────
@router.get(
    "/reviews/history/{submission_id}",
    response_model=APIResponse[List[ReviewHistoryItem]],
    summary="Get complete review, decision, and override history for a submission",
)
async def get_submission_review_history(
    submission_id: str,
    current_user: User = Depends(require_roles("admin", "reviewer", "auditor")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ReviewHistoryItem]]:
    """Retrieves all reviews, overrides, and audit decisions for a submission."""
    # Fetch reviews
    reviews_res = await db.execute(
        sa.select(Review, User)
        .outerjoin(User, Review.reviewer_id == User.id)
        .where(Review.submission_id == submission_id)
        .order_by(Review.created_at.desc())
    )
    rows = reviews_res.all()

    items: List[ReviewHistoryItem] = []
    for r, u in rows:
        items.append(
            ReviewHistoryItem(
                review_id=r.id,
                submission_id=r.submission_id,
                reviewer_email=u.email if u else current_user.email,
                decision=r.status,
                total_score=r.total_score,
                override_flag=r.override_flag,
                override_reason=r.override_reason,
                decision_rationale=getattr(r, "decision_rationale", None) or r.override_reason,
                uncertainty_status="supported",
                created_at=r.created_at,
            )
        )

    if not items:
        # Check audit events for this submission as history source
        events_res = await db.execute(
            sa.select(AuditEvent)
            .where(
                AuditEvent.target_id == submission_id,
                AuditEvent.event_type.in_(["Reviewer Decision", "Override Recorded", "Submission Analyzed"])
            )
            .order_by(AuditEvent.created_at.desc())
        )
        evts = events_res.scalars().all()
        for e in evts:
            items.append(
                ReviewHistoryItem(
                    review_id=e.id,
                    submission_id=submission_id,
                    reviewer_email=current_user.email,
                    decision=e.description,
                    total_score=0.0,
                    override_flag=e.event_type == "Override Recorded",
                    override_reason=e.decision_rationale if e.event_type == "Override Recorded" else None,
                    decision_rationale=e.decision_rationale,
                    uncertainty_status=e.uncertainty_status or "supported",
                    created_at=e.created_at,
                )
            )

    return APIResponse(data=items, message="Submission review history retrieved")
