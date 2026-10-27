from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UncertaintyStatus(str, Enum):
    SUPPORTED = "supported"
    INCONCLUSIVE = "inconclusive"
    NOT_CONFIGURED = "not_configured"
    FAILED = "failed"


class EvidenceReference(BaseModel):
    reference_type: str = Field(..., description="'sentence_offset', 'time_range', 'frame_reference', 'passage_hash'")
    identifier: str
    location: Optional[str] = None
    snippet_hash: Optional[str] = None
    note: Optional[str] = None


class AuditEventBase(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=100)
    target_type: str = Field(..., min_length=2, max_length=50)
    target_id: str
    description: str
    decision_rationale: Optional[str] = None
    model_version: Optional[str] = None
    uncertainty_status: str = Field(default="supported", pattern="^(supported|inconclusive|not_configured|failed)$")
    rubric_version: Optional[int] = None
    result_version: Optional[str] = "v1"
    evidence_references: Optional[List[Dict[str, Any]]] = None
    raw_metadata: Optional[Dict[str, Any]] = None


class AuditEventCreate(AuditEventBase):
    workspace_id: Optional[str] = None


class AuditEventRead(AuditEventBase):
    id: str
    workspace_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    sha256_hash: str
    prev_hash: Optional[str] = None
    tamper_status: str = "Verified"
    client_ip: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventDetail(AuditEventRead):
    pass


class AuditVerificationResponse(BaseModel):
    chain_verified: bool
    total_events: int
    root_hash: Optional[str] = None
    last_hash: Optional[str] = None
    status: str
    tampered_event_ids: List[str] = Field(default_factory=list)


class ReviewDecisionRequest(BaseModel):
    submission_id: str
    decision: str = Field(..., pattern="^(accepted|rejected|shortlisted|flagged|needs_second_review)$")
    decision_rationale: str = Field(..., min_length=3, description="Reviewer reasoning for decision")
    rubric_id: Optional[str] = None
    score_adjustment: Optional[float] = None
    notes: Optional[str] = None


class ReviewOverrideRequest(BaseModel):
    submission_id: str
    override_decision: str = Field(..., pattern="^(accepted|rejected|shortlisted|flagged|needs_second_review)$")
    override_reason: str = Field(..., min_length=5, description="Mandatory rationale explaining human reviewer override")
    new_total_score: Optional[float] = None
    notes: Optional[str] = None


class ReviewHistoryItem(BaseModel):
    review_id: str
    submission_id: str
    reviewer_email: Optional[str] = None
    decision: str
    total_score: float = 0.0
    override_flag: bool = False
    override_reason: Optional[str] = None
    decision_rationale: Optional[str] = None
    uncertainty_status: str = "supported"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
