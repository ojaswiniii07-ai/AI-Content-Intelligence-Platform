"""
Batch orchestration service.

Simulates asynchronous batch processing with partial-failure support.
When Celery/Redis is available, tasks can be dispatched there instead.
In the current implementation, processing runs synchronously in a background
thread via asyncio.to_thread so the endpoint returns immediately.

Failure semantics
-----------------
* A "partial failure" occurs when some submissions fail while others succeed.
  The batch reaches status="partial_failure" (not "failed") and
  failure_details records the per-submission errors.
* A total failure (all submissions fail) sets status="failed".
* An empty batch remains "queued" but is immediately marked "done" with
  processed_items=0.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.batch import SCORE_BUCKETS


# ── Simulated per-submission processing ───────────────────────────────────────

def _simulate_submission_analysis(
    sub_id: str,
    content_type: str,
    analysis_types: List[str],
    force_fail: bool = False,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Simulate analysis of a single submission.

    Returns
    -------
    (success, error_message, result_data)
    """
    if force_fail:
        return False, "Simulated processing failure (corrupted content)", None

    # Random inconclusive / partial flag for realism
    rand = random.random()
    confidence = round(random.uniform(10, 95), 1)
    inconclusive = rand < 0.12  # 12 % inconclusive rate
    flagged = confidence > 60 and not inconclusive

    result: Dict[str, Any] = {
        "submission_id": sub_id,
        "content_type": content_type,
        "status": "inconclusive" if inconclusive else ("flagged" if flagged else "completed"),
        "confidence_pct": confidence,
        "inconclusive": inconclusive,
        "flagged": flagged,
    }

    if "media" in analysis_types and content_type in ("image", "video", "audio"):
        result["media_flagged"] = random.random() < 0.15

    if "text" in analysis_types and content_type == "text":
        result["similarity_pct"] = round(random.uniform(0, 40), 1)

    if "rubric" in analysis_types:
        result["rubric_score_pct"] = round(random.uniform(30, 100), 1)

    return True, None, result


# ── Batch runner ──────────────────────────────────────────────────────────────

async def run_batch_async(
    batch: Dict[str, Any],
    submissions: List[Dict[str, Any]],
    analysis_types: Optional[List[str]] = None,
    rubric_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run asynchronous batch processing and return updated batch state.

    Parameters
    ----------
    batch:
        Current batch dict (id, name, total_items, …).
    submissions:
        List of submission dicts.  Each must have at minimum:
        {"id": str, "content_type": str, "status": str}.
    analysis_types:
        Which analysis dimensions to run.  Defaults to ["text"].
    rubric_id:
        Optional rubric to apply.

    Returns
    -------
    Updated batch state dict with all progress counters updated.
    """
    types = analysis_types or batch.get("analysis_types") or ["text"]
    if rubric_id:
        batch = {**batch, "rubric_id": rubric_id}

    total = len(submissions)
    processed = 0
    failed = 0
    flagged = 0
    failure_details: List[Dict[str, Any]] = []
    confidence_scores: List[float] = []
    distribution: Dict[str, int] = {b: 0 for b in SCORE_BUCKETS}

    # Offload CPU-bound simulation to thread pool
    loop = asyncio.get_event_loop()

    for sub in submissions:
        sub_id = sub.get("id", str(uuid.uuid4()))
        content_type = sub.get("content_type", "text")

        # Introduce ~8 % artificial failure rate for realism
        force_fail = sub.get("_force_fail", False) or (random.random() < 0.08)

        success, err_msg, result = await loop.run_in_executor(
            None,
            _simulate_submission_analysis,
            sub_id,
            content_type,
            types,
            force_fail,
        )

        if success and result:
            processed += 1
            if result.get("flagged"):
                flagged += 1
            conf = result.get("confidence_pct", 0.0)
            confidence_scores.append(conf)
            # Bucket
            if conf < 20:
                distribution["0-20%"] += 1
            elif conf < 40:
                distribution["20-40%"] += 1
            elif conf < 60:
                distribution["40-60%"] += 1
            elif conf < 80:
                distribution["60-80%"] += 1
            else:
                distribution["80-100%"] += 1
        else:
            failed += 1
            failure_details.append({
                "submission_id": sub_id,
                "error": err_msg or "Unknown error",
                "step": "batch_analysis",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    # Determine final batch status
    if total == 0:
        final_status = "done"
    elif failed == total:
        final_status = "failed"
    elif failed > 0:
        final_status = "partial_failure"
    else:
        final_status = "done"

    mean_conf = (
        round(sum(confidence_scores) / len(confidence_scores), 1)
        if confidence_scores else 0.0
    )

    return {
        **batch,
        "status": final_status,
        "total_items": total,
        "processed_items": processed,
        "failed_items": failed,
        "flagged_items": flagged,
        "mean_confidence": mean_conf,
        "score_distribution": distribution,
        "failure_details": failure_details if failure_details else None,
        "analysis_types": types,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
