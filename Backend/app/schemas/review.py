from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CriterionEvaluation(BaseModel):
    criterion_key: str
    criterion_title: str
    score: float = Field(..., ge=0.0)
    max_score: float = Field(default=10.0, gt=0.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_score: float = Field(..., ge=0.0)
    evidence_excerpts: List[str] = Field(default_factory=list, description="Passages cited from submission as evidence")
    explanation: str = Field(..., description="Evaluator explanation for this criterion")
    missing_requirements: List[str] = Field(default_factory=list, description="Unmet requirements or benchmarks")


class StyleEvaluation(BaseModel):
    score: float = 10.0
    passed: bool = True
    word_count: int = 0
    violations: List[str] = Field(default_factory=list)
    observations: str = "Style rules satisfied."


class DecoupledSignals(BaseModel):
    quality_score: float
    rubric_compliance: str = "Full"
    ai_signal: str = "Unanalyzed"  # Low, Medium, High, Unanalyzed
    ai_score: float = 0.0
    similarity_score: float = 0.0
    decoupling_note: str = (
        "Core answer quality and rubric scores are strictly decoupled from AI-involvement "
        "and similarity flags. No score is lowered solely due to an AI detector flag."
    )


class EvaluationResult(BaseModel):
    submission_id: str
    submission_title: str
    rubric_id: str
    rubric_name: str
    rubric_version: int
    total_score: float = Field(..., ge=0.0, le=100.0, description="Weighted percentage score (0-100)")
    criterion_scores: List[CriterionEvaluation]
    style_evaluation: Optional[StyleEvaluation] = None
    missing_requirements: List[str] = Field(default_factory=list)
    signals: DecoupledSignals
    evaluator_metadata: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_incomplete: bool = False


class ShortlistedCandidateItem(BaseModel):
    id: str
    rank: str  # "#1", "#2"
    name: str
    relevance: float = 0.0
    reasoning: float = 0.0
    originality: float = 0.0
    total: float = 0.0
    ai_signal: str = "Low"  # Low, Medium, High
    ai_score: float = 0.0
    status: str = "pending"  # shortlisted, pending, flagged, rejected
    summary: str = ""
    # Additional intelligence attributes
    criterion_breakdown: Optional[Dict[str, float]] = None
    is_incomplete: bool = False
    missing_requirements_count: int = 0
    tie_broken: bool = False
    tie_break_reason: Optional[str] = None
    override_flag: bool = False
    override_reason: Optional[str] = None
    similarity_score: float = 0.0


ShortlistCandidateItem = ShortlistedCandidateItem


class BatchEvaluationRequest(BaseModel):
    rubric_id: str
    workspace_id: Optional[str] = None
    submission_ids: Optional[List[str]] = None
    submissions_inline: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Inline submissions for direct batch evaluation: [{'id': 'sub_1', 'title': '...', 'text': '...'}]"
    )
    evaluator_type: str = Field(default="heuristic", description="'heuristic' or 'llm'")


class BatchEvaluationResponse(BaseModel):
    rubric_id: str
    rubric_name: str
    evaluated_count: int
    evaluations: List[EvaluationResult]
    shortlist: List[ShortlistedCandidateItem]


class ShortlistOverrideRequest(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(shortlisted|pending|flagged|rejected)$")
    new_total_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    override_reason: str = Field(..., min_length=3, description="Mandatory rationale explaining manual reviewer override")
    notes: Optional[str] = None


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
    criterion_scores: Optional[List[Dict[str, Any]]] = None
    missing_requirements: Optional[List[str]] = None
    evaluation_metadata: Optional[Dict[str, Any]] = None
    ai_signal: Optional[str] = None
    ai_score: Optional[float] = None
    similarity_score: Optional[float] = None
    rank: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
