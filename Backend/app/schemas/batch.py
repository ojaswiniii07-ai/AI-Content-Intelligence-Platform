from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class BatchBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    source_type: str = Field(default="Direct Upload", max_length=100)
    file_url: Optional[str] = None


class BatchCreate(BatchBase):
    workspace_id: str


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    processed_items: Optional[int] = None
    flagged_items: Optional[int] = None
    mean_confidence: Optional[float] = None
    score_distribution: Optional[Dict[str, int]] = None


class BatchRead(BatchBase):
    id: str
    workspace_id: str
    total_items: int
    processed_items: int
    flagged_items: int
    mean_confidence: float
    status: str
    progress_percentage: float = 0.0
    score_distribution: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CohortIntegrityReport(BaseModel):
    batch_id: str
    batch_name: str
    total_items: int
    flagged_items: int
    prevalence_pct: float
    mean_confidence_pct: float
    distribution_histogram: Dict[str, int]
    recommendation: str
