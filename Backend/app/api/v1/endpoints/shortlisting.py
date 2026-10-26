from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.review import ShortlistedCandidateItem

router = APIRouter(prefix="/shortlisting", tags=["Shortlisting"])


class StatusUpdateRequest(BaseModel):
    status: str  # shortlisted, pending, flagged, rejected
    override_reason: Optional[str] = None


@router.get("/projects")
async def get_shortlist_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[Dict[str, Any]]]:
    """Returns active shortlisting rubric cohorts and candidate volume."""
    projects = [
        {"id": "p1", "name": "Hackathon 2026 — Final Round", "count": 84, "status": "In progress", "color": "purple"},
        {"id": "p2", "name": "Engineering Hiring Q4", "count": 231, "status": "Reviewing", "color": "cyan"},
        {"id": "p3", "name": "University Essay Competition", "count": 1204, "status": "Complete", "color": "green"},
        {"id": "p4", "name": "Media Grant Applications", "count": 47, "status": "Draft", "color": "orange"},
    ]
    return APIResponse(data=projects, message="Projects retrieved")


@router.get("/submissions", response_model=APIResponse[List[ShortlistedCandidateItem]])
async def get_shortlist_submissions(
    project_id: Optional[str] = Query("p1"),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("score_desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ShortlistedCandidateItem]]:
    """
    Returns candidate submissions scored against calibrated rubrics.
    Decouples rubric quality score from AI involvement signal.
    """
    candidates = [
        ShortlistedCandidateItem(
            id="sub_0041",
            rank="#1",
            name="Team Nexus",
            relevance=9.2,
            reasoning=8.8,
            originality=9.5,
            total=91.7,
            ai_signal="Low",
            ai_score=18.0,
            status="shortlisted",
            summary="Proposes multi-agent consensus verification with verifiable cryptographic watermarking.",
        ),
        ShortlistedCandidateItem(
            id="sub_0027",
            rank="#2",
            name="DataForge",
            relevance=8.5,
            reasoning=9.0,
            originality=7.8,
            total=84.4,
            ai_signal="Medium",
            ai_score=54.0,
            status="pending",
            summary="Analyzes statistical burstiness and semantic perplexity distributions across edge devices.",
        ),
        ShortlistedCandidateItem(
            id="sub_0012",
            rank="#3",
            name="AISolve Co.",
            relevance=8.8,
            reasoning=7.5,
            originality=6.2,
            total=74.2,
            ai_signal="High",
            ai_score=82.0,
            status="flagged",
            summary="Generic architectural boilerplate with high AI sentence repetition cues. Quality is moderate.",
        ),
        ShortlistedCandidateItem(
            id="sub_0089",
            rank="#4",
            name="Quantum Leap",
            relevance=7.9,
            reasoning=8.2,
            originality=8.4,
            total=81.7,
            ai_signal="Low",
            ai_score=24.0,
            status="shortlisted",
            summary="Empirical benchmark analyzing multimodal vision transformer artifacts.",
        ),
        ShortlistedCandidateItem(
            id="sub_0063",
            rank="#5",
            name="BuildRight",
            relevance=7.2,
            reasoning=6.8,
            originality=7.7,
            total=71.9,
            ai_signal="Low",
            ai_score=31.0,
            status="pending",
            summary="Practical enterprise deployment case study. Good structure, moderate reasoning rigor.",
        ),
    ]

    # Filter
    if status and status != "all":
        candidates = [c for c in candidates if c.status == status]

    # Sort
    if sort_by == "score_desc":
        candidates.sort(key=lambda x: x.total, reverse=True)
    elif sort_by == "score_asc":
        candidates.sort(key=lambda x: x.total)
    elif sort_by == "ai_desc":
        candidates.sort(key=lambda x: x.ai_score, reverse=True)
    elif sort_by == "ai_asc":
        candidates.sort(key=lambda x: x.ai_score)

    return APIResponse(data=candidates, message="Submissions retrieved successfully")


@router.patch("/submissions/{submission_id}/status")
async def update_submission_status(
    submission_id: str,
    update_req: StatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """Updates candidate status with optional reviewer override rationale."""
    return APIResponse(
        data={"submission_id": submission_id, "new_status": update_req.status, "updated_by": current_user.email},
        message=f"Submission {submission_id} updated to {update_req.status}",
    )
