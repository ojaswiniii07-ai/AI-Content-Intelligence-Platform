"""
Batch export service — CSV and JSON with spreadsheet formula-injection protection.

Security: CWE-1236 (CSV Injection / Formula Injection)
--------
Any exported field value whose string representation begins with one of the
characters  =  +  -  @  TAB  CR  is prefixed with a single-quote  '
before being written to the CSV.  This prevents Microsoft Excel, LibreOffice
Calc, and Google Sheets from interpreting the cell as a formula when the user
opens the file.

References
----------
* OWASP CSV Injection: https://owasp.org/www-community/attacks/CSV_Injection
* CWE-1236: Improper Neutralization of Formula Elements in a CSV File
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Characters that trigger formula execution in common spreadsheet applications
_FORMULA_TRIGGER_CHARS: str = "=+-@\t\r"


# ── Sanitizer ─────────────────────────────────────────────────────────────────

def sanitize_csv_cell(value: Any) -> str:
    """
    Coerce *value* to a safe string for CSV export.

    If the resulting string starts with a formula-trigger character
    (=, +, -, @, TAB, CR), prefix it with a single-quote  '  so that
    spreadsheet applications treat it as a text literal rather than a formula.

    Parameters
    ----------
    value:
        Any Python value (str, int, float, bool, None, list, dict, …).

    Returns
    -------
    str
        A safe, spreadsheet-injection-free string.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        raw = json.dumps(value, ensure_ascii=False)
    else:
        raw = str(value)
    if raw and raw[0] in _FORMULA_TRIGGER_CHARS:
        return "'" + raw
    return raw


# ── CSV generator ─────────────────────────────────────────────────────────────

_BATCH_CSV_HEADERS: List[str] = [
    "batch_id",
    "batch_name",
    "source_type",
    "status",
    "total_items",
    "processed_items",
    "failed_items",
    "flagged_items",
    "mean_confidence_pct",
    "prevalence_pct",
    "inconclusive_rate_pct",
    "failure_rate_pct",
    "privacy_suppressed",
    "score_0_20",
    "score_20_40",
    "score_40_60",
    "score_60_80",
    "score_80_100",
    "text_ai_mean_pct",
    "media_anomaly_rate_pct",
    "text_similarity_mean_pct",
    "rubric_compliance_mean_pct",
    "analysis_types",
    "authorship_disclaimer",
    "export_timestamp",
]

_SUBMISSION_CSV_HEADERS: List[str] = [
    "submission_id",
    "batch_id",
    "title",
    "content_type",
    "source_identifier",
    "status",
    "word_count",
    "created_at",
]


def generate_batch_csv(
    batch_data: Dict[str, Any],
    submission_rows: Optional[List[Dict[str, Any]]] = None,
    report: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a formula-injection-safe CSV string for a batch export.

    The output contains two sections separated by an empty row:
    1. Batch-level aggregate summary row.
    2. Per-submission rows (if *submission_rows* is provided).

    Parameters
    ----------
    batch_data:
        Dict with standard batch fields (id, name, status, …).
    submission_rows:
        Optional list of dicts with per-submission fields.
    report:
        Optional CohortIntegrityReport dict for richer aggregate fields.

    Returns
    -------
    str
        RFC 4180 CSV with formula-injection protection applied to every cell.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\r\n")

    # ── Batch summary header ──────────────────────────────────────────────────
    writer.writerow([sanitize_csv_cell(h) for h in _BATCH_CSV_HEADERS])

    dist = batch_data.get("score_distribution") or {}
    dim = report.get("dimension_breakdown", {}) if report else {}
    if isinstance(dim, dict):
        dim_get = lambda k: dim.get(k)
    else:
        # Pydantic model
        dim_get = lambda k: getattr(dim, k, None)

    writer.writerow([
        sanitize_csv_cell(batch_data.get("id")),
        sanitize_csv_cell(batch_data.get("name")),
        sanitize_csv_cell(batch_data.get("source_type")),
        sanitize_csv_cell(batch_data.get("status")),
        sanitize_csv_cell(batch_data.get("total_items", 0)),
        sanitize_csv_cell(batch_data.get("processed_items", 0)),
        sanitize_csv_cell(batch_data.get("failed_items", 0)),
        sanitize_csv_cell(batch_data.get("flagged_items", 0)),
        sanitize_csv_cell(batch_data.get("mean_confidence", 0.0)),
        sanitize_csv_cell(report.get("prevalence_pct", 0) if report else ""),
        sanitize_csv_cell(report.get("inconclusive_rate_pct", 0) if report else ""),
        sanitize_csv_cell(report.get("failure_rate_pct", 0) if report else ""),
        sanitize_csv_cell(report.get("privacy_suppressed", False) if report else ""),
        sanitize_csv_cell(dist.get("0-20%", "")),
        sanitize_csv_cell(dist.get("20-40%", "")),
        sanitize_csv_cell(dist.get("40-60%", "")),
        sanitize_csv_cell(dist.get("60-80%", "")),
        sanitize_csv_cell(dist.get("80-100%", "")),
        sanitize_csv_cell(dim_get("text_ai_mean_pct")),
        sanitize_csv_cell(dim_get("media_anomaly_rate_pct")),
        sanitize_csv_cell(dim_get("text_similarity_mean_pct")),
        sanitize_csv_cell(dim_get("rubric_compliance_mean_pct")),
        sanitize_csv_cell(batch_data.get("analysis_types")),
        sanitize_csv_cell(
            "Aggregate cohort statistics must not be used to infer individual "
            "authorship, authenticity, or guilt."
        ),
        sanitize_csv_cell(datetime.now(timezone.utc).isoformat()),
    ])

    # ── Per-submission rows ───────────────────────────────────────────────────
    if submission_rows:
        writer.writerow([])  # blank separator row
        writer.writerow([sanitize_csv_cell(h) for h in _SUBMISSION_CSV_HEADERS])
        for sub in submission_rows:
            writer.writerow([
                sanitize_csv_cell(sub.get("id")),
                sanitize_csv_cell(sub.get("batch_id")),
                sanitize_csv_cell(sub.get("title")),
                sanitize_csv_cell(sub.get("content_type")),
                sanitize_csv_cell(sub.get("source_identifier")),
                sanitize_csv_cell(sub.get("status")),
                sanitize_csv_cell(sub.get("word_count", 0)),
                sanitize_csv_cell(sub.get("created_at")),
            ])

    return buf.getvalue()


# ── JSON generator ────────────────────────────────────────────────────────────

def generate_batch_json(
    batch_data: Dict[str, Any],
    submission_rows: Optional[List[Dict[str, Any]]] = None,
    report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a structured JSON export for a batch.

    The JSON export is structurally identical to the API response format;
    formula injection is not a concern for JSON exports, but the authorship
    disclaimer and privacy_suppressed flag are always included.

    Returns
    -------
    dict
        JSON-serialisable export payload.
    """
    return {
        "export_type": "batch_cohort_report",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "authorship_disclaimer": (
            "Aggregate cohort statistics provide population-level distribution "
            "indicators only. They must not be used to infer individual authorship, "
            "authenticity, or guilt."
        ),
        "batch": batch_data,
        "cohort_report": report,
        "submissions": submission_rows or [],
    }
