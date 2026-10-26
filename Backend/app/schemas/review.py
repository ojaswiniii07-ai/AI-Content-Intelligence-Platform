from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    relevance_score: float = Field(ge=0.0, le=10.0)
    reasoning_score: float = Field(ge=0.0, le=10.0)
    originality_score: float = Field(ge=0.0, le=10.0)
    status: str = Field(default="pending", pattern="^(shortlisted|pending|flagged|rejected)$")
    override_flag: bool = False
    override_reason: Optional[str] = None
    notes: Optional[str] = None


class ReviewCreate(ReviewBase):
    submission_id: str
    rubric_id: Optional[str] = None


class ReviewUpdate(BaseModel):
    relevance_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    reasoning_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    originality_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    status: Optional[str] = Field(default=None, pattern="^(shortlisted|pending|flagged|rejected)$")
    override_flag: Optional[bool] = None
    override_reason: Optional[str] = None
    notes: Optional[str] = None


class ReviewRead(ReviewBase):
    id: str
    submission_id: str
    reviewer_id: str
    rubric_id: Optional[str] = None
    total_score: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShortlistedCandidateItem(BaseModel):
    id: str
    rank: str
    name: str
    relevance: float
    reasoning: float
    originality: float
    total: float
    ai_signal: str  # Low, Medium, High
    ai_score: float
    status: str
    summary: str
