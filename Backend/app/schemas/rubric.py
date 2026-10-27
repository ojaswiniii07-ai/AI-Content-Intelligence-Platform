from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScoringLevel(BaseModel):
    score: float
    label: str
    description: Optional[str] = None


class ScoringScale(BaseModel):
    min_score: float = 0.0
    max_score: float = 10.0
    step: float = 0.5
    levels: Optional[List[ScoringLevel]] = None


class StyleRules(BaseModel):
    min_words: Optional[int] = None
    max_words: Optional[int] = None
    tone: Optional[str] = None  # e.g. "academic", "professional", "technical"
    required_sections: Optional[List[str]] = None
    forbidden_phrases: Optional[List[str]] = None


class CriterionDefinition(BaseModel):
    key: str = Field(..., min_length=1, max_length=64, description="Unique identifier for the criterion")
    title: str = Field(..., min_length=2, max_length=128)
    description: str = Field(..., min_length=1, max_length=2000)
    weight: float = Field(..., gt=0.0, le=1.0, description="Criterion weight between 0 and 1.0")
    min_score: float = Field(default=0.0, ge=0.0)
    max_score: float = Field(default=10.0, gt=0.0)
    required: bool = Field(default=True, description="Whether addressing this criterion is mandatory")
    benchmarks: Optional[List[str]] = Field(default=None, description="Expected points, keywords, or evidence to look for")

    @model_validator(mode="after")
    def validate_scores(self) -> CriterionDefinition:
        if self.min_score >= self.max_score:
            raise ValueError(f"Criterion '{self.key}': min_score ({self.min_score}) must be strictly less than max_score ({self.max_score})")
        return self


def validate_criteria_weights(criteria: List[CriterionDefinition]) -> tuple[bool, List[str], List[str]]:
    """
    Validates a set of criteria:
    1. At least 1 criterion
    2. Unique keys
    3. Positive weights
    4. Weights sum to 1.0 (within 0.005 tolerance)
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not criteria:
        errors.append("Rubric must contain at least one criterion.")
        return False, errors, warnings

    seen_keys = set()
    total_weight = 0.0

    for c in criteria:
        if c.key in seen_keys:
            errors.append(f"Duplicate criterion key: '{c.key}'. Keys must be unique.")
        seen_keys.add(c.key)

        if c.weight <= 0.0:
            errors.append(f"Criterion '{c.key}' weight must be greater than 0.")
        total_weight += c.weight

    if abs(total_weight - 1.0) > 0.005:
        errors.append(f"Total weights must sum to 1.0 (100%). Current sum is {round(total_weight, 4)}.")

    return len(errors) == 0, errors, warnings


class RubricBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    criteria: List[CriterionDefinition] = Field(
        default_factory=lambda: [
            CriterionDefinition(key="relevance", title="Relevance", description="Direct addressing of the prompt/problem statement", weight=0.35),
            CriterionDefinition(key="reasoning", title="Reasoning Depth", description="Analytical rigor, clarity of arguments, and evidence backing", weight=0.35),
            CriterionDefinition(key="originality", title="Originality & Novelty", description="Fresh perspective, innovative approach, non-boilerplate content", weight=0.30),
        ]
    )
    scoring_scale: Optional[ScoringScale] = Field(default_factory=ScoringScale)
    style_rules: Optional[StyleRules] = None
    is_default: bool = False

    @model_validator(mode="after")
    def check_weights(self) -> RubricBase:
        if self.criteria:
            is_valid, errors, _ = validate_criteria_weights(self.criteria)
            if not is_valid:
                raise ValueError("; ".join(errors))
        return self


class RubricCreate(RubricBase):
    workspace_id: str


class RubricUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    criteria: Optional[List[CriterionDefinition]] = None
    scoring_scale: Optional[ScoringScale] = None
    style_rules: Optional[StyleRules] = None
    is_default: Optional[bool] = None

    @model_validator(mode="after")
    def check_weights(self) -> RubricUpdate:
        if self.criteria is not None:
            is_valid, errors, _ = validate_criteria_weights(self.criteria)
            if not is_valid:
                raise ValueError("; ".join(errors))
        return self


class RubricRead(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    version: int = 1
    status: str = "draft"
    parent_rubric_id: Optional[str] = None
    created_by_id: Optional[str] = None
    weights: Dict[str, float]
    criteria: List[CriterionDefinition]
    scoring_scale: Optional[ScoringScale] = None
    style_rules: Optional[StyleRules] = None
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RubricValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    total_weight: float
    criteria_count: int


class RubricPreviewRequest(BaseModel):
    sample_text: str = Field(..., min_length=10, description="Sample response text to test against the rubric")
    title: Optional[str] = "Sample Submission Preview"
    evaluator_type: str = Field(default="heuristic", description="'heuristic' or 'llm'")


class RubricValidateRequest(BaseModel):
    name: Optional[str] = "Validation Draft"
    description: Optional[str] = None
    workspace_id: Optional[str] = None
    criteria: List[CriterionDefinition] = Field(default_factory=list)
    scoring_scale: Optional[ScoringScale] = None
    style_rules: Optional[StyleRules] = None
    is_default: bool = False

