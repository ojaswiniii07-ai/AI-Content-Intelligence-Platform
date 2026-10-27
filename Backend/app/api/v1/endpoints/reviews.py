from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.api.deps import get_current_user, get_db, require_roles
from app.models.review import Review
from app.models.user import User
from app.schemas.audit import (
    ReviewDecisionRequest,
    ReviewHistoryItem,
    ReviewOverrideRequest,
)
from app.schemas.common import APIResponse
from app.schemas.review import ReviewRead
from app.api.v1.endpoints.audit import (
    record_reviewer_decision,
    record_reviewer_override,
    get_submission_review_history,
)

router = APIRouter(prefix="/reviews", tags=["Human Review"])

# Mount decision, override, and history endpoints directly under /reviews
router.add_api_route("/decision", record_reviewer_decision, methods=["POST"], summary="Record reviewer decision")
router.add_api_route("/override", record_reviewer_override, methods=["POST"], summary="Record reviewer override")
router.add_api_route("/history/{submission_id}", get_submission_review_history, methods=["GET"], summary="Get review history for submission")


@router.get("", response_model=APIResponse[List[ReviewRead]], summary="List all human reviews")
async def list_reviews(
    status_filter: Optional[str] = Query(None, alias="status"),
    submission_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("admin", "reviewer", "auditor")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ReviewRead]]:
    """Lists reviews filtered by status or submission. Requires reviewer/auditor/admin role."""
    stmt = sa.select(Review).order_by(Review.updated_at.desc())
    if status_filter:
        stmt = stmt.where(Review.status == status_filter)
    if submission_id:
        stmt = stmt.where(Review.submission_id == submission_id)

    res = await db.execute(stmt)
    reviews = res.scalars().all()
    return APIResponse(
        data=[ReviewRead.model_validate(r) for r in reviews],
        message="Reviews retrieved successfully",
    )
