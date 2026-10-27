from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User
from app.models.rubric import Rubric
from app.schemas.common import APIResponse
from app.schemas.rubric import (
    RubricCreate,
    RubricPreviewRequest,
    RubricRead,
    RubricUpdate,
    RubricValidateRequest,
    RubricValidationResult,
    validate_criteria_weights,
)
from app.schemas.review import EvaluationResult
from app.services.evaluation.registry import get_evaluator
from app.services.evaluation.base import EvaluatorUnavailableError

router = APIRouter(prefix="/rubrics", tags=["Rubrics"])


@router.post(
    "/validate",
    response_model=APIResponse[RubricValidationResult],
    summary="Validate rubric criteria and weights without persisting",
)
async def validate_rubric_definition(
    req: RubricValidateRequest,
    current_user: User = Depends(get_current_user),
) -> APIResponse[RubricValidationResult]:
    """Validates criteria weights, scoring scales, and required fields."""
    valid, errors, warnings = validate_criteria_weights(req.criteria)
    total_w = sum(c.weight for c in req.criteria)
    return APIResponse(
        data=RubricValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            total_weight=round(total_w, 4),
            criteria_count=len(req.criteria),
        ),
        message="Rubric validation completed",
    )


@router.post(
    "",
    response_model=APIResponse[RubricRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new evaluation rubric",
)
async def create_rubric(
    req: RubricCreate,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RubricRead]:
    """
    Creates a new evaluation rubric in 'draft' status.
    Criteria weights must sum to 1.0 (100%).
    """
    valid, errors, _ = validate_criteria_weights(req.criteria)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid rubric criteria: {'; '.join(errors)}",
        )

    # Weights mapping for fast lookup / backward compatibility
    weights_map = {c.key: c.weight for c in req.criteria}
    criteria_dicts = [c.model_dump() for c in req.criteria]
    scale_dict = req.scoring_scale.model_dump() if req.scoring_scale else None
    style_dict = req.style_rules.model_dump() if req.style_rules else None

    rubric_id = str(uuid.uuid4())
    new_rubric = Rubric(
        id=rubric_id,
        workspace_id=req.workspace_id,
        name=req.name,
        description=req.description,
        version=1,
        status="draft",
        parent_rubric_id=None,
        created_by_id=str(current_user.id),
        weights=weights_map,
        criteria=criteria_dicts,
        scoring_scale=scale_dict,
        style_rules=style_dict,
        is_default=req.is_default,
    )
    db.add(new_rubric)
    await db.commit()
    await db.refresh(new_rubric)

    return APIResponse(data=RubricRead.model_validate(new_rubric), message="Rubric created successfully")


@router.get(
    "",
    response_model=APIResponse[List[RubricRead]],
    summary="List rubrics for a workspace",
)
async def list_rubrics(
    workspace_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[RubricRead]]:
    query = sa.select(Rubric)
    if workspace_id:
        query = query.where(Rubric.workspace_id == workspace_id)
    if status_filter:
        query = query.where(Rubric.status == status_filter)
    query = query.order_by(Rubric.updated_at.desc())

    result = await db.execute(query)
    rubrics = result.scalars().all()
    return APIResponse(
        data=[RubricRead.model_validate(r) for r in rubrics],
        message="Rubrics retrieved successfully",
    )


@router.get(
    "/{rubric_id}",
    response_model=APIResponse[RubricRead],
    summary="Get rubric by ID",
)
async def get_rubric(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RubricRead]:
    result = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    rubric = result.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    return APIResponse(data=RubricRead.model_validate(rubric), message="Rubric retrieved")


@router.put(
    "/{rubric_id}",
    response_model=APIResponse[RubricRead],
    summary="Update rubric with automatic versioning for published rubrics",
)
async def update_rubric(
    rubric_id: str,
    req: RubricUpdate,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RubricRead]:
    """
    Updates a rubric.
    If rubric is 'draft', it is modified in place.
    If rubric is already 'published', a new version is created (parent_rubric_id set to original),
    preserving the published historical baseline.
    """
    result = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    new_criteria = req.criteria if req.criteria is not None else existing.criteria
    if req.criteria is not None:
        valid, errors, _ = validate_criteria_weights(req.criteria)
        if not valid:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="; ".join(errors))
        criteria_dicts = [c.model_dump() for c in req.criteria]
        weights_map = {c.key: c.weight for c in req.criteria}
    else:
        criteria_dicts = existing.criteria
        weights_map = existing.weights

    scale_dict = req.scoring_scale.model_dump() if req.scoring_scale is not None else existing.scoring_scale
    style_dict = req.style_rules.model_dump() if req.style_rules is not None else existing.style_rules
    new_name = req.name if req.name is not None else existing.name
    new_desc = req.description if req.description is not None else existing.description
    new_default = req.is_default if req.is_default is not None else existing.is_default

    if existing.status == "published":
        # Create a new version
        new_version_rubric = Rubric(
            id=str(uuid.uuid4()),
            workspace_id=existing.workspace_id,
            name=new_name,
            description=new_desc,
            version=existing.version + 1,
            status="draft",
            parent_rubric_id=existing.id,
            created_by_id=str(current_user.id),
            weights=weights_map,
            criteria=criteria_dicts,
            scoring_scale=scale_dict,
            style_rules=style_dict,
            is_default=new_default,
        )
        db.add(new_version_rubric)
        await db.commit()
        await db.refresh(new_version_rubric)
        return APIResponse(
            data=RubricRead.model_validate(new_version_rubric),
            message=f"Created new draft version (v{new_version_rubric.version}) from published rubric.",
        )
    else:
        # Update existing draft
        existing.name = new_name
        existing.description = new_desc
        existing.weights = weights_map
        existing.criteria = criteria_dicts
        existing.scoring_scale = scale_dict
        existing.style_rules = style_dict
        existing.is_default = new_default
        await db.commit()
        await db.refresh(existing)
        return APIResponse(data=RubricRead.model_validate(existing), message="Draft rubric updated successfully")


@router.post(
    "/{rubric_id}/publish",
    response_model=APIResponse[RubricRead],
    summary="Publish a draft rubric for active evaluations",
)
async def publish_rubric(
    rubric_id: str,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RubricRead]:
    result = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    rubric = result.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    if not rubric.criteria:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot publish a rubric without criteria.")

    rubric.status = "published"
    await db.commit()
    await db.refresh(rubric)
    return APIResponse(data=RubricRead.model_validate(rubric), message=f"Rubric '{rubric.name}' v{rubric.version} published.")


@router.post(
    "/{rubric_id}/preview",
    response_model=APIResponse[EvaluationResult],
    summary="Preview rubric evaluation on a sample submission text without saving",
)
async def preview_rubric_evaluation(
    rubric_id: str,
    req: RubricPreviewRequest,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvaluationResult]:
    """Tests rubric scoring against sample text without persisting evaluation records."""
    result = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    rubric = result.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    try:
        evaluator = get_evaluator(req.evaluator_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        eval_result = await evaluator.evaluate(
            submission_id="preview_sample",
            submission_title=req.title or "Preview Sample",
            submission_text=req.sample_text,
            rubric_data={
                "id": rubric.id,
                "name": rubric.name,
                "version": rubric.version,
                "criteria": rubric.criteria,
                "weights": rubric.weights,
                "scoring_scale": rubric.scoring_scale,
                "style_rules": rubric.style_rules,
            },
        )
    except EvaluatorUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return APIResponse(data=eval_result, message="Preview evaluation completed")


@router.get(
    "/{rubric_id}/versions",
    response_model=APIResponse[List[RubricRead]],
    summary="Get all versions in this rubric's lineage",
)
async def get_rubric_versions(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[RubricRead]]:
    # Find current or root
    curr_res = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    curr = curr_res.scalars().first()
    if not curr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    # Find root
    root_id = curr.parent_rubric_id or curr.id
    # Fetch all with this root or pointing to root
    versions_res = await db.execute(
        sa.select(Rubric)
        .where(sa.or_(Rubric.id == root_id, Rubric.parent_rubric_id == root_id, Rubric.parent_rubric_id == curr.id))
        .order_by(Rubric.version.asc())
    )
    versions = versions_res.scalars().all()
    if not versions:
        versions = [curr]

    return APIResponse(data=[RubricRead.model_validate(v) for v in versions], message="Version history retrieved")


@router.delete(
    "/{rubric_id}",
    response_model=APIResponse[Dict[str, Any]],
    summary="Delete draft rubric or archive published rubric",
)
async def delete_rubric(
    rubric_id: str,
    current_user: User = Depends(require_roles("admin", "reviewer")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    result = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    rubric = result.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    if rubric.status == "published":
        rubric.status = "archived"
        await db.commit()
        return APIResponse(data={"id": rubric_id, "status": "archived"}, message="Published rubric archived.")
    else:
        await db.delete(rubric)
        await db.commit()
        return APIResponse(data={"id": rubric_id, "status": "deleted"}, message="Draft rubric deleted.")
