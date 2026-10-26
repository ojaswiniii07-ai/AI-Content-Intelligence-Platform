from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|archived|draft)$")
    settings: Optional[dict] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[dict] = None


class WorkspaceRead(WorkspaceBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
