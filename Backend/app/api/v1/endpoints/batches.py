import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.batch import BatchCreate, BatchRead, CohortIntegrityReport
from app.schemas.common import APIResponse

router = APIRouter(prefix="/batches", tags=["Batch Processing"])

MOCK_BATCHES = [
    {
        "id": "b1",
        "workspace_id": "ws_default",
        "name": "hackathon-2026-final",
        "source_type": "CSV Upload",
        "file_url": None,
        "total_items": 84,
        "processed_items": 84,
        "flagged_items": 18,
        "mean_confidence": 68.0,
        "status": "done",
        "progress_percentage": 100.0,
        "score_distribution": {"0-20%": 42, "20-40%": 26, "40-60%": 12, "60-80%": 13, "80-100%": 7},
        "created_at": datetime(2026, 10, 26, 18, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 26, 20, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": "b2",
        "workspace_id": "ws_default",
        "name": "eng-hiring-q4-batch",
        "source_type": "Greenhouse API",
        "file_url": None,
        "total_items": 231,
        "processed_items": 180,
        "flagged_items": 32,
        "mean_confidence": 74.0,
        "status": "running",
        "progress_percentage": 78.0,
        "score_distribution": {"0-20%": 50, "20-40%": 22, "40-60%": 14, "60-80%": 10, "80-100%": 4},
        "created_at": datetime(2026, 10, 26, 16, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 26, 20, 30, 0, tzinfo=timezone.utc),
    },
    {
        "id": "b3",
        "workspace_id": "ws_default",
        "name": "university-term-essays-cohort-c",
        "source_type": "Canvas LMS Sync",
        "file_url": None,
        "total_items": 1204,
        "processed_items": 1204,
        "flagged_items": 242,
        "mean_confidence": 81.0,
        "status": "done",
        "progress_percentage": 100.0,
        "score_distribution": {"0-20%": 38, "20-40%": 28, "40-60%": 14, "60-80%": 12, "80-100%": 8},
        "created_at": datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 25, 14, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": "b4",
        "workspace_id": "ws_default",
        "name": "media-grant-proposals-2026",
        "source_type": "S3 Bucket Ingest",
        "file_url": None,
        "total_items": 47,
        "processed_items": 0,
        "flagged_items": 0,
        "mean_confidence": 0.0,
        "status": "queued",
        "progress_percentage": 0.0,
        "score_distribution": {"0-20%": 0, "20-40%": 0, "40-60%": 0, "60-80%": 0, "80-100%": 0},
        "created_at": datetime(2026, 10, 26, 21, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 26, 21, 0, 0, tzinfo=timezone.utc),
    },
]


@router.get("", response_model=APIResponse[List[BatchRead]])
async def list_batches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[BatchRead]]:
    """Lists asynchronous cohort batch orchestration jobs and progress."""
    items = [BatchRead.model_validate(b) for b in MOCK_BATCHES]
    return APIResponse(data=items, message="Batches retrieved")


@router.post("", response_model=APIResponse[BatchRead], status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_in: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchRead]:
    """Queues a new cohort batch for asynchronous processing."""
    now = datetime.now(timezone.utc)
    new_batch = BatchRead(
        id=f"b_{uuid.uuid4().hex[:6]}",
        workspace_id=batch_in.workspace_id,
        name=batch_in.name,
        source_type=batch_in.source_type,
        file_url=batch_in.file_url,
        total_items=120,
        processed_items=0,
        flagged_items=0,
        mean_confidence=0.0,
        status="queued",
        progress_percentage=0.0,
        score_distribution={"0-20%": 0, "20-40%": 0, "40-60%": 0, "60-80%": 0, "80-100%": 0},
        created_at=now,
        updated_at=now,
    )
    return APIResponse(data=new_batch, message="Batch queued for processing")


@router.get("/{batch_id}/report", response_model=APIResponse[CohortIntegrityReport])
async def get_cohort_report(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CohortIntegrityReport]:
    """Generates cohort-level aggregate integrity statistics and distribution histogram."""
    batch = next((b for b in MOCK_BATCHES if b["id"] == batch_id), MOCK_BATCHES[0])
    prevalence = round((batch["flagged_items"] / max(1, batch["total_items"])) * 100, 1)

    report = CohortIntegrityReport(
        batch_id=batch["id"],
        batch_name=batch["name"],
        total_items=batch["total_items"],
        flagged_items=batch["flagged_items"],
        prevalence_pct=prevalence,
        mean_confidence_pct=batch["mean_confidence"],
        distribution_histogram=batch["score_distribution"],
        recommendation="Bimodal score separation suggests natural division between authentic and assisted content.",
    )
    return APIResponse(data=report, message="Cohort report generated")
