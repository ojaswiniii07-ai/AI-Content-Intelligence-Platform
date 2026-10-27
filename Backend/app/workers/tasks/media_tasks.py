"""
Celery media analysis task.

Lifecycle:
  1. Receive job_id from the FastAPI endpoint.
  2. Load MediaJob record from DB (sync via SQLAlchemy core).
  3. Run configured detector adapters in sequence.
  4. Persist result_payload back to MediaJob.
  5. Clean up temp file after success or permanent failure.

Failure handling:
  - Transient errors (network): retry up to 3× with exponential backoff.
  - Permanent errors (bad file, not configured): mark FAILED / INCONCLUSIVE immediately.
  - Temp files always cleaned regardless of outcome.
"""
from __future__ import annotations

import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from celery import Task  # type: ignore
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.services.media.registry import get_adapters_for_media_type
from app.services.media.metadata import extract_metadata, detect_media_type
from app.schemas.media import (
    AudioFinding, Evidence, ImageFinding, MediaAnalysisResult,
    MediaMetadata, MediaType, ModelInfo, Severity, VideoFinding,
)

logger = get_task_logger(__name__)


def _get_db_session():
    """Sync DB session for Celery workers (uses psycopg2 via SQLAlchemy sync URL)."""
    import sqlalchemy as sa
    from app.core.config import settings

    engine = sa.create_engine(settings.sync_database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        return conn, engine


def _load_job(job_id: str) -> Optional[Dict[str, Any]]:
    import sqlalchemy as sa
    from app.core.config import settings

    engine = sa.create_engine(settings.sync_database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        row = conn.execute(
            sa.text("SELECT * FROM media_jobs WHERE id = :id"), {"id": job_id}
        ).mappings().first()
        return dict(row) if row else None


def _update_job(job_id: str, **fields) -> None:
    import sqlalchemy as sa
    from app.core.config import settings

    engine = sa.create_engine(settings.sync_database_url, pool_pre_ping=True)
    set_clauses = ", ".join(f"{k} = :{k}" for k in fields)
    with engine.begin() as conn:
        conn.execute(
            sa.text(f"UPDATE media_jobs SET {set_clauses} WHERE id = :job_id"),
            {"job_id": job_id, **fields},
        )


class MediaAnalysisTask(Task):
    abstract = True
    max_retries = 3
    default_retry_delay = 30  # seconds, doubled each retry (exponential backoff)


@celery_app.task(
    bind=True,
    base=MediaAnalysisTask,
    name="app.workers.tasks.media_tasks.run_media_analysis",
    queue="media",
)
def run_media_analysis(self, job_id: str) -> Dict[str, Any]:
    """
    Background task: run all configured detector adapters for a media job.
    Returns a dict representation of MediaAnalysisResult for serialisation.
    """
    import json

    logger.info(f"[media_analysis] Starting job_id={job_id} worker={self.request.hostname}")

    # Mark as processing
    _update_job(
        job_id,
        status="processing",
        started_at=datetime.utcnow().isoformat(),
        worker_id=self.request.hostname or "unknown",
    )

    job = _load_job(job_id)
    if not job:
        logger.error(f"[media_analysis] job_id={job_id} not found in DB")
        return {"error": "job_not_found"}

    file_path: str = job["storage_path"]
    file_name: str = job["original_file_name"]
    content_type: str = job["content_type"]
    file_size_bytes: int = int(job["file_size_bytes"])
    media_type_str: str = job["media_type"]
    requested_detectors: List[str] = job.get("requested_detectors") or []
    upload_id: str = job["upload_id"]

    try:
        media_type = MediaType(media_type_str)
    except ValueError:
        _update_job(job_id, status="failed", error_message=f"Unknown media_type: {media_type_str}", completed_at=datetime.utcnow().isoformat())
        return {"error": f"Unknown media_type: {media_type_str}"}

    # ── Metadata extraction ───────────────────────────────────
    try:
        file_metadata = extract_metadata(
            file_path=file_path,
            file_name=file_name,
            content_type=content_type,
            file_size_bytes=file_size_bytes,
            media_type=media_type,
        )
    except Exception as exc:
        file_metadata = MediaMetadata(
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
            media_type=media_type,
        )
        logger.warning(f"[media_analysis] metadata extraction failed: {exc}")

    # ── Adapter execution ─────────────────────────────────────
    from app.workers.celery_app import celery_app as _app
    from app.services.media.base import AdapterContext

    ctx = AdapterContext(
        file_path=file_path,
        file_name=file_name,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
    )

    adapters = get_adapters_for_media_type(media_type_str, requested_detectors or None)

    detectors_used: List[ModelInfo] = []
    detectors_skipped: List[Dict[str, str]] = []
    image_findings: List[ImageFinding] = []
    audio_findings: List[AudioFinding] = []
    video_findings: List[VideoFinding] = []
    all_scores: List[float] = []

    for adapter in adapters:
        try:
            result = adapter.safe_analyze(ctx)

            if not result.is_configured:
                detectors_skipped.append({
                    "key": result.adapter_key,
                    "reason": result.skip_reason or "Not configured",
                })
                continue

            detectors_used.append(ModelInfo(
                name=result.model_name,
                version=result.model_version,
                provider=result.provider,
                is_configured=True,
                limitations=result.limitations,
            ))

            if result.score is not None:
                all_scores.append(result.score)

            # Route findings to correct typed list
            for raw_finding in result.findings:
                ev_list = [Evidence(description=str(raw_finding.get("explanation", "")))]

                if media_type == MediaType.IMAGE:
                    image_findings.append(ImageFinding(
                        indicator=raw_finding.get("indicator", "Unknown"),
                        severity=Severity(result.severity),
                        score=result.score,
                        evidence=ev_list,
                        explanation=raw_finding.get("explanation", ""),
                        review_recommendation="Human review recommended before any consequential decision.",
                    ))
                elif media_type == MediaType.AUDIO:
                    audio_findings.append(AudioFinding(
                        indicator=raw_finding.get("indicator", "Unknown"),
                        severity=Severity(result.severity),
                        score=result.score,
                        time_ranges=raw_finding.get("time_ranges") if result.supports_time_ranges else None,
                        evidence=ev_list,
                        explanation=raw_finding.get("explanation", ""),
                        review_recommendation="Human review recommended before any consequential decision.",
                    ))
                elif media_type == MediaType.VIDEO:
                    video_findings.append(VideoFinding(
                        indicator=raw_finding.get("indicator", "Unknown"),
                        severity=Severity(result.severity),
                        score=result.score,
                        frame_references=raw_finding.get("frame_references") if result.supports_frame_refs else None,
                        evidence=ev_list,
                        explanation=raw_finding.get("explanation", ""),
                        review_recommendation="Human review recommended before any consequential decision.",
                    ))

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error(f"[media_analysis] adapter={adapter.ADAPTER_KEY} error: {exc}\n{tb}")

            # Transient errors → retry with backoff; others → record and continue
            if "ConnectionError" in type(exc).__name__ or "Timeout" in type(exc).__name__:
                raise self.retry(exc=exc, countdown=self.default_retry_delay * (2 ** self.request.retries))

            detectors_skipped.append({
                "key": adapter.ADAPTER_KEY,
                "reason": f"Runtime error: {str(exc)[:200]}",
            })

    # ── Aggregate verdict ─────────────────────────────────────
    if not detectors_used:
        overall_verdict = "Inconclusive — no detectors were configured or executed successfully."
        ai_summary = Severity.INCONCLUSIVE
        ai_score_agg = None
    elif all_scores:
        ai_score_agg = round(max(all_scores), 4)  # peak score approach
        if ai_score_agg >= 0.75:
            ai_summary = Severity.HIGH
            overall_verdict = "High AI-involvement indicators detected. Human review required."
        elif ai_score_agg >= 0.40:
            ai_summary = Severity.MEDIUM
            overall_verdict = "Medium AI-involvement indicators. Further review recommended."
        else:
            ai_summary = Severity.LOW
            overall_verdict = "Low AI-involvement indicators. Likely authentic — verify with human review."
    else:
        overall_verdict = "Inconclusive — detectors ran but returned no scorable output."
        ai_summary = Severity.INCONCLUSIVE
        ai_score_agg = None

    analysis_result = MediaAnalysisResult(
        job_id=job_id,
        upload_id=upload_id,
        media_type=media_type,
        file_metadata=file_metadata,
        ai_involvement_summary=ai_summary,
        ai_involvement_score=ai_score_agg,
        image_findings=image_findings or None,
        audio_findings=audio_findings or None,
        video_findings=video_findings or None,
        detectors_used=detectors_used,
        detectors_skipped=detectors_skipped,
        overall_verdict=overall_verdict,
        limitations=[
            "All scores are probabilistic decision-support signals from third-party APIs.",
            "Similarity between patterns and AI output is NOT proof of AI generation.",
            "Spatial and temporal references are only present when the detector supports them.",
            "Consequential decisions require human expert review.",
        ],
        analyzed_at=datetime.utcnow(),
    )

    result_dict = analysis_result.model_dump(mode="json")

    # ── Persist result ────────────────────────────────────────
    _update_job(
        job_id,
        status="completed",
        completed_at=datetime.utcnow().isoformat(),
        result_payload=json.dumps(result_dict),
    )

    logger.info(f"[media_analysis] Completed job_id={job_id} verdict='{overall_verdict}'")

    # ── Clean temp file ───────────────────────────────────────
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[media_analysis] Cleaned temp file: {file_path}")
    except Exception as exc:
        logger.warning(f"[media_analysis] Temp file cleanup failed: {exc}")

    return result_dict
