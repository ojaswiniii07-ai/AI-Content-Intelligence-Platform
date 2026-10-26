from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RubricBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    weights: Dict[str, float] = Field(
        default={"relevance": 0.35, "reasoning": 0.35, "originality": 0.30}
    )
    criteria: Optional[List[dict]] = None
    is_default: bool = False


class RubricCreate(RubricBase):
    workspace_id: str


class RubricUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weights: Optional[Dict[str, float]] = None
    criteria: Optional[List[dict]] = None
    is_default: Optional[bool] = None


class RubricRead(RubricBase):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
