"""
Pydantic schemas for Batch Processing and Cohort Reporting.

Design notes
------------
* ScoreDistribution and CohortDimensionBreakdown keep text AI-involvement,
  media anomaly signals, text similarity, and rubric compliance scores in
  separate named fields — they must never be blended or used to infer single-
  submission authorship from group statistics.
* CohortIntegrityReport carries an explicit authorship_disclaimer, metric
  definitions, and privacy-suppression metadata.
* Privacy suppression: if sample_size < PRIVACY_MIN_GROUP_SIZE (5), granular
  score distributions are omitted and privacy_suppressed is set to True.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Constants ─────────────────────────────────────────────────────────────────
PRIVACY_MIN_GROUP_SIZE: int = 5
SCORE_BUCKETS: List[str] = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
VALID_ANALYSIS_TYPES: List[str] = ["text", "media", "rubric"]
VALID_STATUS_VALUES: List[str] = [
    "queued", "running", "done", "failed", "partial_failure",
]


# ── Batch Create / Update / Read ──────────────────────────────────────────────

class BatchCreate(BaseModel):
    """Payload to create a new cohort batch."""
    name: str = Field(min_length=2, max_length=255)
    workspace_id: str
    source_type: str = Field(default="Direct Upload", max_length=100)
    file_url: Optional[str] = None
    analysis_types: Optional[List[str]] = Field(
        default=None,
        description="Ordered list of analysis dimensions: text, media, rubric.",
    )
    rubric_id: Optional[str] = Field(
        default=None,
        description="Optional rubric ID to evaluate submissions against.",
    )

    @field_validator("analysis_types")
    @classmethod
    def validate_analysis_types(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            invalid = [t for t in v if t not in VALID_ANALYSIS_TYPES]
            if invalid:
                raise ValueError(f"Invalid analysis types: {invalid}. Allowed: {VALID_ANALYSIS_TYPES}")
        return v


class BatchUpdate(BaseModel):
    """Partial update of mutable batch fields."""
    name: Optional[str] = None
    status: Optional[str] = None
    processed_items: Optional[int] = None
    failed_items: Optional[int] = None
    flagged_items: Optional[int] = None
    mean_confidence: Optional[float] = None
    score_distribution: Optional[Dict[str, int]] = None
    failure_details: Optional[List[dict]] = None


class BatchRead(BaseModel):
    """Full batch representation returned to API clients."""
    id: str
    workspace_id: str
    name: str
    source_type: str
    file_url: Optional[str] = None
    analysis_types: Optional[List[str]] = None
    rubric_id: Optional[str] = None

    total_items: int
    processed_items: int
    failed_items: int = 0
    flagged_items: int
    mean_confidence: float
    status: str
    progress_percentage: float = 0.0

    score_distribution: Optional[Dict[str, int]] = None
    failure_details: Optional[List[dict]] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBatchesResponse(BaseModel):
    """Paginated list of batches with navigation metadata."""
    items: List[BatchRead]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Submission Attachment ─────────────────────────────────────────────────────

class SubmissionAttachItem(BaseModel):
    """A single submission to attach to a batch."""
    title: str = Field(min_length=1, max_length=255)
    content_type: Literal["text", "image", "video", "audio"] = "text"
    text_content: Optional[str] = Field(
        default=None,
        description="Raw text content (required when content_type=text).",
    )
    file_url: Optional[str] = Field(
        default=None,
        description="URL or path to media file (required when content_type != text).",
    )
    source_identifier: Optional[str] = Field(
        default=None,
        max_length=100,
        description="External reference code, e.g. 'sub_0041'. Used for deduplication.",
    )


class BatchAttachSubmissionsRequest(BaseModel):
    """Request to bulk-attach submissions to an existing batch."""
    submissions: List[SubmissionAttachItem] = Field(min_length=0)


class BatchAttachResponse(BaseModel):
    """Result of a bulk-attach operation."""
    batch_id: str
    added_count: int
    duplicates_skipped: int
    total_items: int
    message: str


# ── Run Request ───────────────────────────────────────────────────────────────

class BatchRunRequest(BaseModel):
    """Optional overrides when triggering a batch run."""
    analysis_types: Optional[List[str]] = None
    rubric_id: Optional[str] = None

    @field_validator("analysis_types")
    @classmethod
    def validate_analysis_types(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            invalid = [t for t in v if t not in VALID_ANALYSIS_TYPES]
            if invalid:
                raise ValueError(f"Invalid analysis types: {invalid}.")
        return v


# ── Cohort Report ─────────────────────────────────────────────────────────────

class ScoreDistribution(BaseModel):
    """
    Histogram of AI-involvement indicator score counts across five equal buckets.

    IMPORTANT: These are population-level indicator distributions.
    Individual bucket counts must NOT be used to identify or profile specific
    submissions or their authors.
    """
    bucket_0_20: int = Field(alias="0-20%", default=0)
    bucket_20_40: int = Field(alias="20-40%", default=0)
    bucket_40_60: int = Field(alias="40-60%", default=0)
    bucket_60_80: int = Field(alias="60-80%", default=0)
    bucket_80_100: int = Field(alias="80-100%", default=0)

    model_config = ConfigDict(populate_by_name=True)


class CohortDimensionBreakdown(BaseModel):
    """
    Dimension-specific aggregate metrics — kept strictly separate to prevent
    conflation of different signal types.

    Field semantics
    ---------------
    text_ai_mean_pct:
        Mean AI-involvement indicator score (%). This is a model-output indicator,
        NOT a calibrated probability. Values depend on the configured detector.
    text_ai_inconclusive_rate_pct:
        Percentage of text submissions where the detector returned 'inconclusive'
        (model unavailable, insufficient evidence, or low-confidence).
    media_anomaly_rate_pct:
        Percentage of media submissions where any synthetic-content indicator was
        flagged. Metadata patterns are supporting evidence only; they are not proof
        of manipulation or AI generation.
    text_similarity_mean_pct:
        Mean passage-similarity score across text submissions. High similarity to
        reference material is NOT evidence of plagiarism on its own.
    rubric_compliance_mean_pct:
        Mean weighted rubric score across evaluated submissions (0–100 %).
        A rubric score does NOT incorporate AI-involvement indicators.
    """
    text_ai_mean_pct: Optional[float] = None
    text_ai_inconclusive_rate_pct: Optional[float] = None
    media_anomaly_rate_pct: Optional[float] = None
    text_similarity_mean_pct: Optional[float] = None
    rubric_compliance_mean_pct: Optional[float] = None


class CohortStatistics(BaseModel):
    """Descriptive statistics for a numeric metric across a cohort."""
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    sample_size: int


class MetricDefinition(BaseModel):
    """Human-readable definition of a reported metric."""
    name: str
    description: str
    unit: str
    limitations: str


class CohortIntegrityReport(BaseModel):
    """
    Aggregate cohort-level report — suitable for authorized reviewers.

    Privacy guarantees
    ------------------
    * Granular score distributions are suppressed (privacy_suppressed=True) when
      total_items < 5 to prevent re-identification of individual submissions.
    * This report provides population-level statistics only.
    * The authorship_disclaimer field contains the mandatory prohibition against
      inferring individual authorship or culpability from these statistics.

    Signal separation
    -----------------
    text_ai, media_anomaly, text_similarity, and rubric_compliance are reported
    in separate dimension_breakdown fields. They must never be combined into a
    single "integrity score" or used to automatically reject submissions.
    """
    batch_id: str
    batch_name: str
    analysis_types: Optional[List[str]] = None

    # Counts
    total_items: int
    sample_size: int = 0
    processed_items: int
    failed_items: int = 0
    flagged_items: int
    inconclusive_items: int = 0

    # Rates (percentages, 0–100)
    prevalence_pct: float = Field(
        description="Percentage of submissions where any indicator was flagged."
    )
    mean_confidence_pct: float = Field(
        description="Mean AI-involvement indicator score across text submissions (%)."
    )
    inconclusive_rate_pct: float = Field(
        description="Percentage of submissions returning inconclusive status."
    )
    failure_rate_pct: float = Field(
        description="Percentage of submissions where processing failed."
    )

    # Score distribution (suppressed for small cohorts)
    score_distribution: Optional[Dict[str, int]] = None
    confidence_statistics: Optional[CohortStatistics] = None

    # Privacy suppression
    privacy_suppressed: bool = Field(
        default=False,
        description=(
            "True when granular distributions are suppressed because sample_size < 5, "
            "to prevent re-identification of individual submissions."
        ),
    )
    suppression_reason: Optional[str] = None

    # Per-dimension breakdown (decoupled signals)
    dimension_breakdown: CohortDimensionBreakdown

    # Metric glossary
    metric_definitions: List[MetricDefinition]

    # Mandatory disclaimer
    authorship_disclaimer: str = Field(
        default=(
            "Aggregate cohort statistics provide population-level distribution indicators "
            "only. They must not be used to infer individual authorship, authenticity, or "
            "guilt. No submission should be rejected or penalised based solely on cohort-"
            "level statistics or detector indicator scores."
        )
    )
