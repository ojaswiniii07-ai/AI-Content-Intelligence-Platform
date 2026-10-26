from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class IntegrationBase(BaseModel):
    provider: str = Field(min_length=2, max_length=100)
    config: Optional[dict] = None
    is_active: bool = True


class IntegrationCreate(IntegrationBase):
    workspace_id: str


class IntegrationUpdate(BaseModel):
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class IntegrationRead(IntegrationBase):
    id: str
    workspace_id: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
