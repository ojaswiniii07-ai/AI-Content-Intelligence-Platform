"""
Cohort reporting engine.

Computes aggregate statistics from a batch and its associated submissions.
Applies privacy suppression (k-anonymity / cell suppression) when the cohort
is too small to report granular distributions safely.

Design constraints
------------------
* Text AI-involvement, media anomaly signals, text similarity, and rubric scores
  are computed and returned in *separate* dimension fields.  They must never be
  blended into a single "integrity score".
* Authorship disclaimer is always attached to every report.
* Any cohort with sample_size < PRIVACY_MIN_GROUP_SIZE receives
  privacy_suppressed=True and granular distributions are omitted.
* No individual submission is identified in the report output.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Optional

from app.schemas.batch import (
    PRIVACY_MIN_GROUP_SIZE,
    CohortDimensionBreakdown,
    CohortIntegrityReport,
    CohortStatistics,
    MetricDefinition,
)

# ── Metric glossary ────────────────────────────────────────────────────────────

METRIC_DEFINITIONS: List[MetricDefinition] = [
    MetricDefinition(
        name="prevalence_pct",
        description=(
            "Percentage of submissions in this cohort where at least one indicator "
            "threshold was reached.  This is a model-output indicator, not a proven "
            "finding of AI generation or plagiarism."
        ),
        unit="percent (0–100)",
        limitations=(
            "Detector accuracy varies by model version, domain, and text length. "
            "False positives and false negatives are possible."
        ),
    ),
    MetricDefinition(
        name="mean_confidence_pct",
        description=(
            "Mean AI-involvement indicator score across text submissions.  The score "
            "is a model output — it is NOT a calibrated probability.  Values depend on "
            "the configured detector and its training distribution."
        ),
        unit="percent (0–100)",
        limitations=(
            "Scores are NOT calibrated probabilities.  They reflect the configured "
            "detector's internal scoring and should not be treated as ground truth."
        ),
    ),
    MetricDefinition(
        name="inconclusive_rate_pct",
        description=(
            "Percentage of submissions where the analysis returned inconclusive status "
            "(model unavailable, insufficient evidence, or low-confidence output)."
        ),
        unit="percent (0–100)",
        limitations="A high inconclusive rate may indicate a configuration issue.",
    ),
    MetricDefinition(
        name="score_distribution",
        description=(
            "Histogram of AI-involvement indicator scores across five equal-width "
            "buckets (0-20 %, 20-40 %, 40-60 %, 60-80 %, 80-100 %).  Shows the "
            "shape of the indicator score distribution across this cohort."
        ),
        unit="count of submissions per bucket",
        limitations=(
            "Suppressed when sample_size < 5 to prevent re-identification of "
            "individual submissions."
        ),
    ),
    MetricDefinition(
        name="text_ai_mean_pct",
        description=(
            "Mean AI-involvement indicator score across text submissions.  Kept "
            "separate from media anomaly, similarity, and rubric scores."
        ),
        unit="percent (0–100)",
        limitations="Same as mean_confidence_pct — scores are not calibrated probabilities.",
    ),
    MetricDefinition(
        name="media_anomaly_rate_pct",
        description=(
            "Percentage of media submissions where any synthetic-content indicator was "
            "raised.  Metadata anomalies are supporting evidence — not proof."
        ),
        unit="percent (0–100)",
        limitations=(
            "Media anomaly detection depends on available adapters and configured "
            "providers.  Returns not_configured if no adapter is available."
        ),
    ),
    MetricDefinition(
        name="text_similarity_mean_pct",
        description=(
            "Mean passage-similarity score (Jaccard / cosine similarity against "
            "configured reference material) across text submissions.  High similarity "
            "is NOT evidence of plagiarism."
        ),
        unit="percent (0–100)",
        limitations=(
            "Similarity depends on reference corpus coverage.  No reference corpus "
            "returns not_configured."
        ),
    ),
    MetricDefinition(
        name="rubric_compliance_mean_pct",
        description=(
            "Mean weighted rubric score (0–100 %) across evaluated submissions.  "
            "Rubric scores reflect rubric-defined quality criteria and are independent "
            "of AI-involvement indicator values."
        ),
        unit="percent (0–100)",
        limitations="Rubric score does not incorporate AI-involvement indicators.",
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_pct(numerator: float, denominator: float) -> float:
    """Return percentage rounded to 1 decimal, zero when denominator is 0."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _compute_statistics(values: List[float]) -> Optional[CohortStatistics]:
    """Return descriptive statistics for a list of numeric values."""
    n = len(values)
    if n == 0:
        return None
    mean = round(sum(values) / n, 2)
    median = round(statistics.median(values), 2)
    std_dev = round(statistics.pstdev(values), 2) if n > 1 else 0.0
    return CohortStatistics(
        mean=mean,
        median=median,
        std_dev=std_dev,
        min_val=round(min(values), 2),
        max_val=round(max(values), 2),
        sample_size=n,
    )


def _bucket_label(score_pct: float) -> str:
    """Map a 0–100 score to the correct 20-point histogram bucket label."""
    if score_pct < 20:
        return "0-20%"
    if score_pct < 40:
        return "20-40%"
    if score_pct < 60:
        return "40-60%"
    if score_pct < 80:
        return "60-80%"
    return "80-100%"


def _empty_distribution() -> Dict[str, int]:
    return {"0-20%": 0, "20-40%": 0, "40-60%": 0, "60-80%": 0, "80-100%": 0}


# ── Main report builder ───────────────────────────────────────────────────────

def build_cohort_report(
    batch: Any,
    submission_records: Optional[List[Dict[str, Any]]] = None,
) -> CohortIntegrityReport:
    """
    Build a CohortIntegrityReport from a Batch ORM object (or dict-like object)
    and an optional list of per-submission result dicts.

    Parameters
    ----------
    batch:
        Batch ORM instance or dict with the standard batch fields.
    submission_records:
        Optional list of dicts; each dict may contain:
            - "confidence_pct": float   (text AI-involvement indicator, 0–100)
            - "status": str             (submission status)
            - "content_type": str       (text | image | video | audio)
            - "media_flagged": bool     (True if any media indicator raised)
            - "similarity_pct": float   (text similarity score, 0–100)
            - "rubric_score_pct": float (rubric compliance score, 0–100)
            - "inconclusive": bool      (True if analysis was inconclusive)
            - "failed": bool            (True if processing failed)
            - "flagged": bool           (True if any indicator threshold reached)

    Returns
    -------
    CohortIntegrityReport
        Fully constructed report.  Granular distributions suppressed if
        total_items < PRIVACY_MIN_GROUP_SIZE.
    """
    # Normalise batch fields whether ORM object or dict
    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    batch_id: str = str(_get(batch, "id", "unknown"))
    batch_name: str = str(_get(batch, "name", "Unknown Batch"))
    total_items: int = int(_get(batch, "total_items", 0))
    processed_items: int = int(_get(batch, "processed_items", total_items))
    failed_items: int = int(_get(batch, "failed_items", 0))
    flagged_items: int = int(_get(batch, "flagged_items", 0))
    mean_confidence: float = float(_get(batch, "mean_confidence", 0.0))
    analysis_types: Optional[List[str]] = _get(batch, "analysis_types", None)
    stored_distribution: Optional[Dict[str, int]] = _get(batch, "score_distribution", None)

    # ── Compute from submission records if provided ────────────────────────────
    confidence_values: List[float] = []
    similarity_values: List[float] = []
    rubric_values: List[float] = []
    inconclusive_count: int = 0
    media_flagged_count: int = 0
    media_submission_count: int = 0
    distribution: Dict[str, int] = _empty_distribution()

    if submission_records:
        for rec in submission_records:
            ct = rec.get("content_type", "text")
            conf = rec.get("confidence_pct")
            if conf is not None:
                confidence_values.append(float(conf))
                distribution[_bucket_label(float(conf))] += 1
            if rec.get("similarity_pct") is not None:
                similarity_values.append(float(rec["similarity_pct"]))
            if rec.get("rubric_score_pct") is not None:
                rubric_values.append(float(rec["rubric_score_pct"]))
            if rec.get("inconclusive"):
                inconclusive_count += 1
            if ct in ("image", "video", "audio"):
                media_submission_count += 1
                if rec.get("media_flagged"):
                    media_flagged_count += 1
    else:
        # Fallback to batch-level aggregates already stored
        distribution = stored_distribution or _empty_distribution()
        if mean_confidence:
            # Reconstruct a synthetic single data-point for statistics
            confidence_values = [mean_confidence]

    # ── Rates ─────────────────────────────────────────────────────────────────
    prevalence_pct = _safe_pct(flagged_items, total_items)
    effective_mean = (
        round(sum(confidence_values) / len(confidence_values), 1)
        if confidence_values else mean_confidence
    )
    inconclusive_rate_pct = _safe_pct(inconclusive_count, max(1, processed_items))
    failure_rate_pct = _safe_pct(failed_items, max(1, total_items))

    # ── Privacy suppression ───────────────────────────────────────────────────
    privacy_suppressed = total_items < PRIVACY_MIN_GROUP_SIZE
    suppression_reason: Optional[str] = None
    reported_distribution: Optional[Dict[str, int]] = None
    confidence_stats: Optional[CohortStatistics] = None

    if privacy_suppressed:
        suppression_reason = (
            f"Granular score distributions suppressed: cohort contains {total_items} "
            f"submission(s), below the minimum group size of {PRIVACY_MIN_GROUP_SIZE} "
            "required to prevent re-identification of individual submissions."
        )
    else:
        reported_distribution = distribution
        confidence_stats = _compute_statistics(confidence_values)

    # ── Dimension breakdown (decoupled signals) ───────────────────────────────
    dimension_breakdown = CohortDimensionBreakdown(
        text_ai_mean_pct=round(effective_mean, 1) if not privacy_suppressed else None,
        text_ai_inconclusive_rate_pct=(
            round(inconclusive_rate_pct, 1) if not privacy_suppressed else None
        ),
        media_anomaly_rate_pct=(
            _safe_pct(media_flagged_count, media_submission_count)
            if media_submission_count > 0 and not privacy_suppressed
            else None
        ),
        text_similarity_mean_pct=(
            round(sum(similarity_values) / len(similarity_values), 1)
            if similarity_values and not privacy_suppressed
            else None
        ),
        rubric_compliance_mean_pct=(
            round(sum(rubric_values) / len(rubric_values), 1)
            if rubric_values and not privacy_suppressed
            else None
        ),
    )

    return CohortIntegrityReport(
        batch_id=batch_id,
        batch_name=batch_name,
        analysis_types=analysis_types,
        total_items=total_items,
        sample_size=total_items,
        processed_items=processed_items,
        failed_items=failed_items,
        flagged_items=flagged_items,
        inconclusive_items=inconclusive_count,
        prevalence_pct=prevalence_pct,
        mean_confidence_pct=effective_mean,
        inconclusive_rate_pct=inconclusive_rate_pct,
        failure_rate_pct=failure_rate_pct,
        score_distribution=reported_distribution,
        confidence_statistics=confidence_stats,
        privacy_suppressed=privacy_suppressed,
        suppression_reason=suppression_reason,
        dimension_breakdown=dimension_breakdown,
        metric_definitions=METRIC_DEFINITIONS,
    )
