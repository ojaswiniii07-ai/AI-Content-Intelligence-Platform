"""
Media Analysis API — endpoints for upload, submit, status, result, delete.

Two-phase flow:
  POST /media/upload       → upload file, get upload_id
  POST /media/submit       → create analysis job, enqueue Celery task
  GET  /media/jobs/{job_id}        → job status
  GET  /media/jobs/{job_id}/result → full analysis result
  DELETE /media/jobs/{job_id}      → cancel/delete job + file
  GET  /media/jobs                 → history (paginated)
  GET  /media/adapters             → registry summary

All endpoints require authentication.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.media import (
    JobStatus,
    MediaAnalysisResult,
    MediaJobStatusResponse,
    MediaJobSubmitRequest,
    MediaType,
    MediaUploadResponse,
)
from app.services.media.metadata import detect_media_type
from app.services.media.registry import list_all_adapters
from app.services.media.storage import delete_file, get_upload_dir, write_temp_file

router = APIRouter(prefix="/media", tags=["Media Analysis"])

# ── Config limits ─────────────────────────────────────────────
MAX_IMAGE_MB = int(getattr(settings, "MEDIA_MAX_IMAGE_MB", 20))
MAX_AUDIO_MB = int(getattr(settings, "MEDIA_MAX_AUDIO_MB", 100))
MAX_VIDEO_MB = int(getattr(settings, "MEDIA_MAX_VIDEO_MB", 500))

ALLOWED_CONTENT_TYPES = {
    "image": ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/tiff"],
    "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/flac", "audio/aac", "audio/mp4"],
    "video": ["video/mp4", "video/webm", "video/mpeg", "video/quicktime", "video/x-msvideo"],
}
ALL_ALLOWED_TYPES: List[str] = sum(ALLOWED_CONTENT_TYPES.values(), [])


def _size_limit_bytes(media_type: MediaType) -> int:
    limits = {
        MediaType.IMAGE: MAX_IMAGE_MB * 1024 * 1024,
        MediaType.AUDIO: MAX_AUDIO_MB * 1024 * 1024,
        MediaType.VIDEO: MAX_VIDEO_MB * 1024 * 1024,
    }
    return limits.get(media_type, 50 * 1024 * 1024)


# ── Helpers ───────────────────────────────────────────────────
async def _get_job_row(job_id: str, db: AsyncSession) -> Dict[str, Any]:
    row = (await db.execute(
        sa.text("SELECT * FROM media_jobs WHERE id = :id"), {"id": job_id}
    )).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Media job '{job_id}' not found.")
    return dict(row)


async def _assert_owner(job: Dict, current_user: User) -> None:
    if str(job["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied — this job belongs to another user.")


# ── 1. Upload ─────────────────────────────────────────────────
@router.post(
    "/upload",
    response_model=APIResponse[MediaUploadResponse],
    summary="Upload a media file for analysis",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_media_file(
    file: UploadFile = File(..., description="Image, audio, or video file"),
    workspace_id: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
) -> APIResponse[MediaUploadResponse]:
    """
    Phase 1 of 2. Upload a file to private storage and receive an `upload_id`.
    Call `/media/submit` with this ID to start analysis.

    - Validates content-type and file magic bytes header.
    - Enforces per-type size limits.
    - File is stored privately — not accessible via any public URL.
    """
    content_type = (file.content_type or "").split(";")[0].strip().lower()

    # Validate content type
    if content_type not in ALL_ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported media type '{content_type}'. "
                f"Allowed: {', '.join(ALL_ALLOWED_TYPES)}"
            ),
        )

    media_type = detect_media_type(content_type)
    if media_type is None:
        raise HTTPException(status_code=415, detail=f"Cannot determine media type for '{content_type}'.")

    # Read file content
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Validate magic bytes (minimal check)
    _validate_magic_bytes(file_bytes, media_type, content_type)

    # Size limit
    size_limit = _size_limit_bytes(media_type)
    if len(file_bytes) > size_limit:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large for {media_type.value}: "
                f"{len(file_bytes) / 1024 / 1024:.1f}MB > limit {size_limit // 1024 // 1024}MB."
            ),
        )

    # Write to private storage
    try:
        upload_id, storage_path, expires_at = write_temp_file(
            data=file_bytes,
            original_name=file.filename or f"upload.{content_type.split('/')[-1]}",
            content_type=content_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Storage write failed: {exc}")

    return APIResponse(
        data=MediaUploadResponse(
            upload_id=upload_id,
            file_name=file.filename or "unknown",
            media_type=media_type,
            file_size_bytes=len(file_bytes),
            storage_path=storage_path,
            expires_at=expires_at,
        ),
        message="File uploaded. Call /media/submit to start analysis.",
    )


def _validate_magic_bytes(data: bytes, media_type: MediaType, content_type: str) -> None:
    """
    Check the first few bytes for well-known magic numbers.
    Raises 400 if the file content clearly doesn't match the declared type.
    This is a basic guard — not a deep content scan.
    """
    header = data[:12]
    # JPEG: FF D8 FF
    if content_type == "image/jpeg" and not header[:3] == b"\xff\xd8\xff":
        raise HTTPException(400, "File content does not match declared image/jpeg type.")
    # PNG: 89 50 4E 47
    if content_type == "image/png" and not header[:4] == b"\x89PNG":
        raise HTTPException(400, "File content does not match declared image/png type.")
    # MP4: ftyp at offset 4
    if content_type == "video/mp4" and b"ftyp" not in header:
        # Some MP4s have moov before ftyp — be lenient (just check first 20 bytes)
        extended = data[:20]
        if b"ftyp" not in extended and b"mdat" not in extended:
            raise HTTPException(400, "File does not appear to be a valid MP4.")
    # WebM: 1A 45 DF A3
    if content_type == "video/webm" and header[:4] != b"\x1a\x45\xdf\xa3":
        raise HTTPException(400, "File content does not match declared video/webm type.")


# ── 2. Submit for analysis ─────────────────────────────────────
@router.post(
    "/submit",
    response_model=APIResponse[MediaJobStatusResponse],
    summary="Submit an uploaded file for asynchronous analysis",
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_media_analysis(
    req: MediaJobSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MediaJobStatusResponse]:
    """
    Phase 2 of 2. Submit the uploaded file (by upload_id) for analysis.
    Returns a job_id. Poll `/media/jobs/{job_id}` for status.

    If Celery/Redis is unavailable, job is marked FAILED immediately.
    """
    from app.services.media.storage import get_upload_dir
    import pathlib

    # Verify upload_id maps to an existing file by checking storage
    upload_dir = get_upload_dir()
    matching_files = list(upload_dir.glob(f"{req.upload_id}*"))
    if not matching_files:
        raise HTTPException(
            status_code=404,
            detail=f"upload_id '{req.upload_id}' not found. File may have expired or was already processed.",
        )

    storage_path = str(matching_files[0])
    file_name = matching_files[0].name
    content_type = _guess_content_type(matching_files[0].suffix)
    media_type = detect_media_type(content_type)
    if media_type is None:
        raise HTTPException(status_code=415, detail="Cannot determine media type from uploaded file.")

    file_size_bytes = matching_files[0].stat().st_size
    job_id = str(uuid.uuid4())

    # Insert job record
    await db.execute(
        sa.text("""
            INSERT INTO media_jobs (
                id, upload_id, user_id, workspace_id,
                original_file_name, file_size_bytes, content_type, media_type,
                storage_path, status, requested_detectors, submitted_at,
                request_metadata
            ) VALUES (
                :id, :upload_id, :user_id, :workspace_id,
                :original_file_name, :file_size_bytes, :content_type, :media_type,
                :storage_path, 'pending', :requested_detectors, :submitted_at,
                :request_metadata
            )
        """),
        {
            "id": job_id,
            "upload_id": req.upload_id,
            "user_id": str(current_user.id),
            "workspace_id": req.workspace_id,
            "original_file_name": file_name,
            "file_size_bytes": str(file_size_bytes),
            "content_type": content_type,
            "media_type": media_type.value,
            "storage_path": storage_path,
            "requested_detectors": json.dumps(req.detectors),
            "submitted_at": datetime.utcnow().isoformat(),
            "request_metadata": json.dumps(req.metadata),
        },
    )
    await db.commit()

    # Enqueue Celery task
    celery_available = False
    try:
        from app.workers.tasks.media_tasks import run_media_analysis
        task = run_media_analysis.apply_async(args=[job_id], queue="media")
        celery_task_id = task.id
        celery_available = True
        await db.execute(
            sa.text("UPDATE media_jobs SET celery_task_id = :tid WHERE id = :id"),
            {"tid": celery_task_id, "id": job_id},
        )
        await db.commit()
    except Exception as exc:
        # Celery/Redis unavailable — mark failed, don't silently swallow
        await db.execute(
            sa.text("UPDATE media_jobs SET status = 'failed', error_message = :err WHERE id = :id"),
            {"err": f"Celery/Redis unavailable: {str(exc)[:500]}", "id": job_id},
        )
        await db.commit()
        raise HTTPException(
            status_code=503,
            detail=(
                "Analysis job was created but could not be enqueued: Celery/Redis is unavailable. "
                f"Ensure Redis is running at REDIS_URL. Error: {str(exc)[:200]}"
            ),
        )

    return APIResponse(
        data=MediaJobStatusResponse(
            job_id=job_id,
            upload_id=req.upload_id,
            status=JobStatus.PENDING,
            media_type=media_type,
            submitted_at=datetime.utcnow(),
        ),
        message=f"Analysis job queued. Poll GET /api/v1/media/jobs/{job_id} for status.",
    )


def _guess_content_type(suffix: str) -> str:
    mapping = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
        ".tiff": "image/tiff", ".mp3": "audio/mpeg", ".wav": "audio/wav",
        ".ogg": "audio/ogg", ".flac": "audio/flac", ".aac": "audio/aac",
        ".m4a": "audio/mp4", ".mp4": "video/mp4", ".webm": "video/webm",
        ".mpg": "video/mpeg", ".mov": "video/quicktime", ".avi": "video/x-msvideo",
    }
    return mapping.get(suffix.lower(), "application/octet-stream")


# ── 3. Job status ─────────────────────────────────────────────
@router.get(
    "/jobs/{job_id}",
    response_model=APIResponse[MediaJobStatusResponse],
    summary="Get analysis job status",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MediaJobStatusResponse]:
    """Poll this endpoint to track job progress."""
    job = await _get_job_row(job_id, db)
    await _assert_owner(job, current_user)

    def _dt(v) -> Optional[datetime]:
        if not v:
            return None
        return datetime.fromisoformat(str(v)) if isinstance(v, str) else v

    return APIResponse(
        data=MediaJobStatusResponse(
            job_id=job_id,
            upload_id=job["upload_id"],
            status=JobStatus(job["status"]),
            media_type=MediaType(job["media_type"]) if job.get("media_type") else None,
            submitted_at=_dt(job["submitted_at"]) or datetime.utcnow(),
            started_at=_dt(job.get("started_at")),
            completed_at=_dt(job.get("completed_at")),
            worker_id=job.get("worker_id"),
            error_message=job.get("error_message"),
        ),
        message="Job status retrieved.",
    )


# ── 4. Result ─────────────────────────────────────────────────
@router.get(
    "/jobs/{job_id}/result",
    response_model=APIResponse[MediaAnalysisResult],
    summary="Get full analysis result for a completed job",
)
async def get_job_result(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MediaAnalysisResult]:
    """
    Returns the full structured analysis result.
    Only available when job status == 'completed'.
    """
    job = await _get_job_row(job_id, db)
    await _assert_owner(job, current_user)

    if job["status"] == "pending":
        raise HTTPException(status_code=202, detail="Job is still pending. Try again later.")
    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Job is processing. Try again later.")
    if job["status"] == "failed":
        raise HTTPException(
            status_code=422,
            detail=f"Job failed: {job.get('error_message', 'Unknown error')}",
        )

    raw = job.get("result_payload")
    if not raw:
        raise HTTPException(status_code=404, detail="Result not found for this job.")

    result_dict = json.loads(raw) if isinstance(raw, str) else raw
    return APIResponse(
        data=MediaAnalysisResult(**result_dict),
        message="Analysis result retrieved.",
    )


# ── 5. Delete job ─────────────────────────────────────────────
@router.delete(
    "/jobs/{job_id}",
    response_model=APIResponse[Dict[str, str]],
    summary="Delete a job and clean up the associated file",
)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, str]]:
    """
    Deletes the job record and the temporary media file.
    Running jobs will still complete in the worker but results are discarded.
    """
    job = await _get_job_row(job_id, db)
    await _assert_owner(job, current_user)

    # Clean temp file
    if job.get("storage_path"):
        delete_file(job["storage_path"])

    await db.execute(sa.text("DELETE FROM media_jobs WHERE id = :id"), {"id": job_id})
    await db.commit()

    return APIResponse(data={"job_id": job_id, "status": "deleted"}, message="Job and file deleted.")


# ── 6. Job history ─────────────────────────────────────────────
@router.get(
    "/jobs",
    response_model=APIResponse[List[MediaJobStatusResponse]],
    summary="List analysis jobs for the current user (paginated)",
)
async def list_jobs(
    workspace_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[MediaJobStatusResponse]]:
    """Paginated job history for the authenticated user."""
    filters = "WHERE user_id = :user_id"
    params: Dict[str, Any] = {"user_id": str(current_user.id), "limit": limit, "offset": offset}

    if workspace_id:
        filters += " AND workspace_id = :workspace_id"
        params["workspace_id"] = workspace_id
    if status_filter:
        filters += " AND status = :status"
        params["status"] = status_filter

    rows = (await db.execute(
        sa.text(f"""
            SELECT * FROM media_jobs {filters}
            ORDER BY submitted_at DESC LIMIT :limit OFFSET :offset
        """),
        params,
    )).mappings().all()

    def _dt(v):
        if not v:
            return None
        return datetime.fromisoformat(str(v)) if isinstance(v, str) else v

    items = [
        MediaJobStatusResponse(
            job_id=str(r["id"]),
            upload_id=r["upload_id"],
            status=JobStatus(r["status"]),
            media_type=MediaType(r["media_type"]) if r.get("media_type") else None,
            submitted_at=_dt(r["submitted_at"]) or datetime.utcnow(),
            started_at=_dt(r.get("started_at")),
            completed_at=_dt(r.get("completed_at")),
            worker_id=r.get("worker_id"),
            error_message=r.get("error_message"),
        )
        for r in rows
    ]

    return APIResponse(data=items, message=f"{len(items)} jobs returned.")


# ── 7. Adapter registry ────────────────────────────────────────
@router.get(
    "/adapters",
    summary="List all registered detector adapters and their configuration status",
)
async def list_adapters(
    current_user: User = Depends(get_current_user),
) -> APIResponse[List[Dict[str, Any]]]:
    """
    Shows which adapters are registered and whether they are configured.
    Use this to understand what will run before submitting an analysis job.
    """
    return APIResponse(
        data=list_all_adapters(),
        message="Adapter registry retrieved.",
    )
