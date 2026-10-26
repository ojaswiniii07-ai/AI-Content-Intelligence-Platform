from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AuditEventBase(BaseModel):
    event_type: str = Field(min_length=2, max_length=100)
    target_type: str = Field(min_length=2, max_length=50)
    target_id: str
    description: str
    decision_rationale: Optional[str] = None
    model_version: Optional[str] = None


class AuditEventCreate(AuditEventBase):
    workspace_id: Optional[str] = None


class AuditEventRead(AuditEventBase):
    id: str
    workspace_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    sha256_hash: str
    prev_hash: Optional[str] = None
    tamper_status: str
    client_ip: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventDetail(AuditEventRead):
    raw_payload: Optional[dict] = None
