"""
Batch Processing and Cohort Reporting endpoints.

Authorization
-------------
* All endpoints require an authenticated user (Bearer JWT).
* POST /batches, POST /batches/{id}/submissions, POST /batches/{id}/run,
  GET  /batches/{id}/export  require role "admin" or "reviewer".
* GET  /batches and GET /batches/{id}  are accessible to all authenticated users.
* GET  /batches/{id}/report  is accessible to reviewers and admins only.

Privacy guarantees
------------------
* Cohort reports suppress granular score distributions when sample_size < 5.
* No individual submission is identified in aggregate report output.
* The authorship_disclaimer is always embedded in every report response.

Export security
---------------
* CSV exports apply formula-injection protection (CWE-1236): any cell value
  that begins with  =  +  -  @  TAB  CR  is prefixed with  '  before export.
* JSON exports include the same disclaimer and suppression metadata.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User
from app.schemas.batch import (
    BatchAttachResponse,
    BatchAttachSubmissionsRequest,
    BatchCreate,
    BatchRead,
    BatchRunRequest,
    CohortIntegrityReport,
    PaginatedBatchesResponse,
)
from app.schemas.common import APIResponse
from app.services.reporting.batch_runner import run_batch_async
from app.services.reporting.cohort import build_cohort_report
from app.services.reporting.exporter import generate_batch_csv, generate_batch_json

router = APIRouter(prefix="/batches", tags=["Batch Processing"])

# ── In-memory batch store (mock backend until DB is connected) ────────────────
# Keys: batch_id (str)  →  value: dict  (batch state)
_BATCH_STORE: Dict[str, Dict[str, Any]] = {}
# Keys: batch_id (str)  →  value: list of submission dicts
_SUBMISSION_STORE: Dict[str, List[Dict[str, Any]]] = {}


def _seed_demo_data() -> None:
    """Populate mock store with demo batches matching the frontend fixtures."""
    now = datetime.now(timezone.utc)
    demos = [
        {
            "id": "b1",
            "workspace_id": "ws_default",
            "name": "hackathon-2026-final",
            "source_type": "CSV Upload",
            "file_url": None,
            "analysis_types": ["text", "rubric"],
            "rubric_id": None,
            "total_items": 84,
            "processed_items": 84,
            "failed_items": 2,
            "flagged_items": 18,
            "mean_confidence": 68.0,
            "status": "done",
            "progress_percentage": 100.0,
            "score_distribution": {"0-20%": 42, "20-40%": 26, "40-60%": 12, "60-80%": 13, "80-100%": 7},
            "failure_details": None,
            "created_at": datetime(2026, 10, 26, 18, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 10, 26, 20, 0, 0, tzinfo=timezone.utc),
        },
        {
            "id": "b2",
            "workspace_id": "ws_default",
            "name": "eng-hiring-q4-batch",
            "source_type": "Greenhouse API",
            "file_url": None,
            "analysis_types": ["text", "media"],
            "rubric_id": None,
            "total_items": 231,
            "processed_items": 180,
            "failed_items": 5,
            "flagged_items": 32,
            "mean_confidence": 74.0,
            "status": "running",
            "progress_percentage": 78.0,
            "score_distribution": {"0-20%": 50, "20-40%": 22, "40-60%": 14, "60-80%": 10, "80-100%": 4},
            "failure_details": [
                {"submission_id": "s_err_01", "error": "File corrupt", "step": "media_analysis", "timestamp": now.isoformat()},
            ],
            "created_at": datetime(2026, 10, 26, 16, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 10, 26, 20, 30, 0, tzinfo=timezone.utc),
        },
        {
            "id": "b3",
            "workspace_id": "ws_default",
            "name": "university-term-essays-cohort-c",
            "source_type": "Canvas LMS Sync",
            "file_url": None,
            "analysis_types": ["text", "rubric"],
            "rubric_id": None,
            "total_items": 1204,
            "processed_items": 1204,
            "failed_items": 0,
            "flagged_items": 242,
            "mean_confidence": 81.0,
            "status": "done",
            "progress_percentage": 100.0,
            "score_distribution": {"0-20%": 38, "20-40%": 28, "40-60%": 14, "60-80%": 12, "80-100%": 8},
            "failure_details": None,
            "created_at": datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 10, 25, 14, 0, 0, tzinfo=timezone.utc),
        },
        {
            "id": "b4",
            "workspace_id": "ws_default",
            "name": "media-grant-proposals-2026",
            "source_type": "S3 Bucket Ingest",
            "file_url": None,
            "analysis_types": ["media"],
            "rubric_id": None,
            "total_items": 47,
            "processed_items": 0,
            "failed_items": 0,
            "flagged_items": 0,
            "mean_confidence": 0.0,
            "status": "queued",
            "progress_percentage": 0.0,
            "score_distribution": {"0-20%": 0, "20-40%": 0, "40-60%": 0, "60-80%": 0, "80-100%": 0},
            "failure_details": None,
            "created_at": datetime(2026, 10, 26, 21, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 10, 26, 21, 0, 0, tzinfo=timezone.utc),
        },
    ]
    for d in demos:
        _BATCH_STORE[d["id"]] = d
        _SUBMISSION_STORE[d["id"]] = []


_seed_demo_data()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _batch_to_read(b: Dict[str, Any]) -> BatchRead:
    total = b.get("total_items", 0)
    processed = b.get("processed_items", 0)
    pct = round((processed / total) * 100, 1) if total else 0.0
    return BatchRead(
        id=b["id"],
        workspace_id=b["workspace_id"],
        name=b["name"],
        source_type=b.get("source_type", "Direct Upload"),
        file_url=b.get("file_url"),
        analysis_types=b.get("analysis_types"),
        rubric_id=b.get("rubric_id"),
        total_items=total,
        processed_items=processed,
        failed_items=b.get("failed_items", 0),
        flagged_items=b.get("flagged_items", 0),
        mean_confidence=b.get("mean_confidence", 0.0),
        status=b.get("status", "queued"),
        progress_percentage=pct,
        score_distribution=b.get("score_distribution"),
        failure_details=b.get("failure_details"),
        created_at=b.get("created_at", datetime.now(timezone.utc)),
        updated_at=b.get("updated_at", datetime.now(timezone.utc)),
    )


def _get_batch_or_404(batch_id: str) -> Dict[str, Any]:
    batch = _BATCH_STORE.get(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' not found.",
        )
    return batch


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=APIResponse[PaginatedBatchesResponse])
async def list_batches(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    status_filter: Optional[str] = Query(
        default=None, alias="status",
        description="Filter by status: queued | running | done | failed | partial_failure.",
    ),
    analysis_type: Optional[str] = Query(
        default=None,
        description="Filter batches that include this analysis type: text | media | rubric.",
    ),
    date_from: Optional[str] = Query(
        default=None, description="ISO-8601 start date (inclusive), e.g. 2026-10-01."
    ),
    date_to: Optional[str] = Query(
        default=None, description="ISO-8601 end date (inclusive), e.g. 2026-10-31."
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedBatchesResponse]:
    """
    Paginated, filterable list of cohort batches.

    Filters
    -------
    * **status** — queued / running / done / failed / partial_failure
    * **analysis_type** — batches that include the given analysis dimension
    * **date_from / date_to** — ISO-8601 date strings (filter on created_at)
    """
    batches = list(_BATCH_STORE.values())

    # Apply filters
    if status_filter:
        batches = [b for b in batches if b.get("status") == status_filter]
    if analysis_type:
        batches = [
            b for b in batches
            if analysis_type in (b.get("analysis_types") or [])
        ]
    if date_from:
        try:
            df = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
            batches = [b for b in batches if b.get("created_at", datetime.min) >= df]
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
            batches = [b for b in batches if b.get("created_at", datetime.max) <= dt]
        except ValueError:
            pass

    # Sort newest first
    batches.sort(key=lambda b: b.get("created_at", datetime.min), reverse=True)

    # Paginate
    total = len(batches)
    total_pages = max(1, -(-total // page_size))  # ceiling division
    offset = (page - 1) * page_size
    page_items = batches[offset: offset + page_size]

    items = [_batch_to_read(b) for b in page_items]
    return APIResponse(
        data=PaginatedBatchesResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message=f"Retrieved {len(items)} of {total} batches.",
    )


@router.post("", response_model=APIResponse[BatchRead], status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_in: BatchCreate,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchRead]:
    """
    Create and queue a new cohort batch.

    Role required: **admin** or **reviewer**.
    """
    now = datetime.now(timezone.utc)
    batch_id = f"b_{uuid.uuid4().hex[:8]}"
    new_batch: Dict[str, Any] = {
        "id": batch_id,
        "workspace_id": batch_in.workspace_id,
        "name": batch_in.name,
        "source_type": batch_in.source_type,
        "file_url": batch_in.file_url,
        "analysis_types": batch_in.analysis_types or ["text"],
        "rubric_id": batch_in.rubric_id,
        "total_items": 0,
        "processed_items": 0,
        "failed_items": 0,
        "flagged_items": 0,
        "mean_confidence": 0.0,
        "status": "queued",
        "progress_percentage": 0.0,
        "score_distribution": {"0-20%": 0, "20-40%": 0, "40-60%": 0, "60-80%": 0, "80-100%": 0},
        "failure_details": None,
        "created_at": now,
        "updated_at": now,
    }
    _BATCH_STORE[batch_id] = new_batch
    _SUBMISSION_STORE[batch_id] = []
    return APIResponse(data=_batch_to_read(new_batch), message="Batch created and queued.")


@router.get("/{batch_id}", response_model=APIResponse[BatchRead])
async def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchRead]:
    """Retrieve the current status and progress of a single batch."""
    batch = _get_batch_or_404(batch_id)
    return APIResponse(data=_batch_to_read(batch), message="Batch retrieved.")


@router.post(
    "/{batch_id}/submissions",
    response_model=APIResponse[BatchAttachResponse],
    status_code=status.HTTP_200_OK,
)
async def attach_submissions(
    batch_id: str,
    body: BatchAttachSubmissionsRequest,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchAttachResponse]:
    """
    Attach one or more submissions to an existing batch.

    Deduplication
    -------------
    Submissions with the same *source_identifier* are skipped — only the first
    occurrence is added.  Submissions without a source_identifier are always
    added (no deduplication possible).

    Empty lists are accepted (returns added_count=0).
    """
    batch = _get_batch_or_404(batch_id)

    if batch.get("status") not in ("queued",):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot attach submissions to a batch with status='{batch['status']}'. "
                "Only 'queued' batches accept new submissions."
            ),
        )

    existing_subs = _SUBMISSION_STORE.setdefault(batch_id, [])
    existing_identifiers = {
        s["source_identifier"]
        for s in existing_subs
        if s.get("source_identifier")
    }

    added = 0
    duplicates = 0

    for item in body.submissions:
        if item.source_identifier and item.source_identifier in existing_identifiers:
            duplicates += 1
            continue

        sub = {
            "id": f"s_{uuid.uuid4().hex[:8]}",
            "batch_id": batch_id,
            "workspace_id": batch["workspace_id"],
            "title": item.title,
            "content_type": item.content_type,
            "text_content": item.text_content,
            "file_url": item.file_url,
            "source_identifier": item.source_identifier,
            "status": "pending",
            "word_count": len((item.text_content or "").split()),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        existing_subs.append(sub)
        if item.source_identifier:
            existing_identifiers.add(item.source_identifier)
        added += 1

    # Update batch total
    new_total = len(existing_subs)
    batch["total_items"] = new_total
    batch["updated_at"] = datetime.now(timezone.utc)

    return APIResponse(
        data=BatchAttachResponse(
            batch_id=batch_id,
            added_count=added,
            duplicates_skipped=duplicates,
            total_items=new_total,
            message=f"Added {added} submission(s). {duplicates} duplicate(s) skipped.",
        ),
        message=f"Submissions attached. Total: {new_total}.",
    )


@router.post(
    "/{batch_id}/run",
    response_model=APIResponse[BatchRead],
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_batch(
    batch_id: str,
    run_req: Optional[BatchRunRequest] = None,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchRead]:
    """
    Trigger asynchronous batch analysis.

    * If the batch has no attached submissions, it is immediately marked done
      with processed_items=0.
    * Analysis runs asynchronously; the response returns immediately with
      status=running.  Poll GET /batches/{id} for progress.
    * Partial failures (some submissions fail) result in status=partial_failure.

    Role required: **admin** or **reviewer**.
    """
    batch = _get_batch_or_404(batch_id)

    if batch.get("status") == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch is already running.",
        )

    override_types = run_req.analysis_types if run_req else None
    override_rubric = run_req.rubric_id if run_req else None

    submissions = _SUBMISSION_STORE.get(batch_id, [])

    # Handle empty batch
    if not submissions:
        batch.update({
            "status": "done",
            "total_items": 0,
            "processed_items": 0,
            "failed_items": 0,
            "flagged_items": 0,
            "mean_confidence": 0.0,
            "score_distribution": {"0-20%": 0, "20-40%": 0, "40-60%": 0, "60-80%": 0, "80-100%": 0},
            "updated_at": datetime.now(timezone.utc),
        })
        return APIResponse(
            data=_batch_to_read(batch),
            message="Empty batch: no submissions to process. Status set to done.",
        )

    # Mark running immediately
    batch["status"] = "running"
    batch["updated_at"] = datetime.now(timezone.utc)

    # Run processing (awaited here for test-friendliness; in production this
    # would be dispatched to Celery and return immediately)
    updated = await run_batch_async(
        batch=batch,
        submissions=submissions,
        analysis_types=override_types,
        rubric_id=override_rubric,
    )
    _BATCH_STORE[batch_id] = updated
    return APIResponse(
        data=_batch_to_read(updated),
        message=f"Batch analysis complete. Status: {updated['status']}.",
    )


@router.get(
    "/{batch_id}/report",
    response_model=APIResponse[CohortIntegrityReport],
)
async def get_cohort_report(
    batch_id: str,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CohortIntegrityReport]:
    """
    Retrieve aggregate cohort integrity report for a completed batch.

    Privacy
    -------
    Score distributions are suppressed when the cohort has < 5 submissions,
    to prevent re-identification of individual submissions.

    Signal separation
    -----------------
    Text AI-involvement, media anomaly signals, text similarity, and rubric
    compliance are reported in separate dimension_breakdown fields and must
    not be combined or used to infer individual authorship.

    Role required: **admin** or **reviewer**.
    """
    batch = _get_batch_or_404(batch_id)
    submissions = _SUBMISSION_STORE.get(batch_id, [])
    report = build_cohort_report(batch=batch, submission_records=submissions)
    return APIResponse(data=report, message="Cohort report generated.")


@router.get("/{batch_id}/export")
async def export_batch(
    batch_id: str,
    format: str = Query(
        default="json",
        description="Export format: 'csv' or 'json'.",
    ),
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Export batch data and cohort report.

    Formats
    -------
    * **json** — Structured JSON export (Content-Type: application/json).
    * **csv** — RFC 4180 CSV with formula-injection protection applied
                to every cell (Content-Type: text/csv).

    Security
    --------
    CSV exports protect against spreadsheet formula injection (CWE-1236):
    any cell value beginning with  =  +  -  @  TAB  CR  is prefixed with  '

    Role required: **admin** or **reviewer**.
    """
    batch = _get_batch_or_404(batch_id)
    submissions = _SUBMISSION_STORE.get(batch_id, [])
    report = build_cohort_report(batch=batch, submission_records=submissions)
    report_dict = report.model_dump()

    if format.lower() == "csv":
        csv_content = generate_batch_csv(
            batch_data=batch,
            submission_rows=submissions,
            report=report_dict,
        )
        filename = f"batch_{batch_id}_report.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    elif format.lower() == "json":
        json_payload = generate_batch_json(
            batch_data=batch,
            submission_rows=submissions,
            report=report_dict,
        )
        filename = f"batch_{batch_id}_report.json"
        return Response(
            content=json.dumps(json_payload, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Allowed: csv, json.",
        )
