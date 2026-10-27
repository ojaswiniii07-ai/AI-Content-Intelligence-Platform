from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.review import Review
from app.models.rubric import Rubric
from app.models.submission import Submission
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.review import (
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    CriterionEvaluation,
    DecoupledSignals,
    EvaluationResult,
    ReviewRead,
    ShortlistCandidateItem,
    ShortlistedCandidateItem,
    ShortlistOverrideRequest,
    StyleEvaluation,
)
from app.services.audit.service import append_audit_event
from app.services.evaluation.base import EvaluatorUnavailableError
from app.services.evaluation.ranking import rank_and_shortlist
from app.services.evaluation.registry import get_evaluator

router = APIRouter(prefix="/shortlisting", tags=["Shortlisting"])


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(shortlisted|pending|flagged|rejected)$")
    override_reason: Optional[str] = None


# ── 1. Cohort Projects (frontend compatible) ──────────────────────────────────
@router.get("/projects", summary="Returns active shortlisting rubric cohorts and candidate volume")
async def get_shortlist_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[Dict[str, Any]]]:
    """Returns active shortlisting rubric cohorts and candidate volume."""
    # Check if there are real rubrics in DB
    rubrics_res = await db.execute(sa.select(Rubric).order_by(Rubric.created_at.desc()))
    db_rubrics = rubrics_res.scalars().all()

    if db_rubrics:
        projects = []
        colors = ["purple", "cyan", "green", "orange"]
        for idx, r in enumerate(db_rubrics):
            # Count reviews for this rubric
            cnt_res = await db.execute(
                sa.select(sa.func.count(Review.id)).where(Review.rubric_id == r.id)
            )
            count = cnt_res.scalar() or 0
            projects.append({
                "id": r.id,
                "name": r.name,
                "count": count,
                "status": "In progress" if r.status == "published" else r.status.capitalize(),
                "color": colors[idx % len(colors)],
            })
        return APIResponse(data=projects, message="Projects retrieved")

    # Fallback default cohorts for initial demo view
    projects = [
        {"id": "p1", "name": "Hackathon 2026 — Final Round", "count": 84, "status": "In progress", "color": "purple"},
        {"id": "p2", "name": "Engineering Hiring Q4", "count": 231, "status": "Reviewing", "color": "cyan"},
        {"id": "p3", "name": "University Essay Competition", "count": 1204, "status": "Complete", "color": "green"},
        {"id": "p4", "name": "Media Grant Applications", "count": 47, "status": "Draft", "color": "orange"},
    ]
    return APIResponse(data=projects, message="Projects retrieved")


# ── 2. Submissions / Shortlist (frontend compatible + dynamic DB) ──────────────
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
    # Check if project_id matches a real rubric in DB
    reviews_res = await db.execute(
        sa.select(Review, Submission)
        .join(Submission, Review.submission_id == Submission.id)
        .where(Review.rubric_id == project_id)
    )
    db_reviews = reviews_res.all()

    if db_reviews:
        evaluations: List[EvaluationResult] = []
        overrides_map: Dict[str, Dict[str, Any]] = {}

        for rev, sub in db_reviews:
            crit_scores = []
            if rev.criterion_scores:
                for c in rev.criterion_scores:
                    crit_scores.append(CriterionEvaluation.model_validate(c))

            ev = EvaluationResult(
                submission_id=sub.id,
                submission_title=sub.title,
                rubric_id=rev.rubric_id or "",
                rubric_name="Project Rubric",
                rubric_version=1,
                total_score=rev.total_score,
                criterion_scores=crit_scores,
                missing_requirements=rev.missing_requirements or [],
                signals=DecoupledSignals(
                    quality_score=rev.total_score,
                    ai_signal=rev.ai_signal or "Low",
                    ai_score=rev.ai_score or 0.0,
                    similarity_score=rev.similarity_score or 0.0,
                ),
                evaluator_metadata=rev.evaluation_metadata or {},
            )
            evaluations.append(ev)
            overrides_map[sub.id] = {
                "status": rev.status,
                "override_flag": rev.override_flag,
                "override_reason": rev.override_reason,
                "total_score": rev.total_score,
            }

        candidates = rank_and_shortlist(evaluations, status_overrides=overrides_map)
    else:
        # Default baseline candidates for demonstration / demo project
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
    if sort_by in ("score_desc", "score-desc"):
        candidates.sort(key=lambda x: x.total, reverse=True)
    elif sort_by in ("score_asc", "score-asc"):
        candidates.sort(key=lambda x: x.total)
    elif sort_by in ("ai_desc", "ai-desc"):
        candidates.sort(key=lambda x: x.ai_score, reverse=True)
    elif sort_by in ("ai_asc", "ai-asc"):
        candidates.sort(key=lambda x: x.ai_score)

    return APIResponse(data=candidates, message="Submissions retrieved successfully")


# ── 3. Batch Evaluation ────────────────────────────────────────────────────────
@router.post(
    "/evaluate",
    response_model=APIResponse[BatchEvaluationResponse],
    summary="Evaluate multiple submissions against a shared rubric",
)
async def evaluate_submissions_batch(
    req: BatchEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchEvaluationResponse]:
    """
    Evaluates submissions against a shared rubric using specified evaluator ('heuristic' or 'llm').
    Persists reviews in database and returns ranked shortlist with deterministic tie handling.
    """
    rubric_res = await db.execute(sa.select(Rubric).where(Rubric.id == req.rubric_id))
    rubric = rubric_res.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{req.rubric_id}' not found.")

    try:
        evaluator = get_evaluator(req.evaluator_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    rubric_dict = {
        "id": rubric.id,
        "name": rubric.name,
        "version": rubric.version,
        "criteria": rubric.criteria or [],
        "weights": rubric.weights,
        "scoring_scale": rubric.scoring_scale,
        "style_rules": rubric.style_rules,
    }

    # Gather items to evaluate
    items_to_eval = []
    if req.submissions_inline:
        for item in req.submissions_inline:
            items_to_eval.append({
                "id": str(item.get("id", str(uuid.uuid4()))),
                "title": item.get("title", "Inline Submission"),
                "text": item.get("text", ""),
                "ai_context": item.get("ai_context", {}),
            })
    elif req.submission_ids:
        subs_res = await db.execute(sa.select(Submission).where(Submission.id.in_(req.submission_ids)))
        db_subs = subs_res.scalars().all()
        for s in db_subs:
            items_to_eval.append({
                "id": s.id,
                "title": s.title,
                "text": s.text_content or "",
                "ai_context": {},
            })

    if not items_to_eval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No submissions provided. Provide either 'submission_ids' or 'submissions_inline'.",
        )

    evaluations: List[EvaluationResult] = []

    for item in items_to_eval:
        try:
            ev = await evaluator.evaluate(
                submission_id=item["id"],
                submission_title=item["title"],
                submission_text=item["text"],
                rubric_data=rubric_dict,
                ai_context=item.get("ai_context"),
            )
            evaluations.append(ev)
        except EvaluatorUnavailableError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    # Persist or update reviews in DB when real submissions exist
    for ev in evaluations:
        # Check if submission exists in DB
        sub_check = await db.execute(sa.select(Submission).where(Submission.id == ev.submission_id))
        sub_exists = sub_check.scalars().first()

        if sub_exists:
            # Upsert Review
            rev_check = await db.execute(
                sa.select(Review).where(Review.submission_id == ev.submission_id, Review.rubric_id == rubric.id)
            )
            existing_rev = rev_check.scalars().first()

            # Find individual criteria scores
            rel_score = next((c.score for c in ev.criterion_scores if c.criterion_key == "relevance"), 0.0)
            rea_score = next((c.score for c in ev.criterion_scores if c.criterion_key == "reasoning"), 0.0)
            ori_score = next((c.score for c in ev.criterion_scores if c.criterion_key == "originality"), 0.0)

            crit_payload = [c.model_dump() for c in ev.criterion_scores]

            if existing_rev:
                existing_rev.total_score = ev.total_score
                existing_rev.relevance_score = rel_score
                existing_rev.reasoning_score = rea_score
                existing_rev.originality_score = ori_score
                existing_rev.criterion_scores = crit_payload
                existing_rev.missing_requirements = ev.missing_requirements
                existing_rev.evaluation_metadata = ev.evaluator_metadata
                existing_rev.ai_signal = ev.signals.ai_signal
                existing_rev.ai_score = ev.signals.ai_score
                existing_rev.similarity_score = ev.signals.similarity_score
            else:
                new_rev = Review(
                    id=str(uuid.uuid4()),
                    submission_id=ev.submission_id,
                    reviewer_id=str(current_user.id),
                    rubric_id=rubric.id,
                    relevance_score=rel_score,
                    reasoning_score=rea_score,
                    originality_score=ori_score,
                    total_score=ev.total_score,
                    status="shortlisted" if ev.total_score >= 80.0 else "pending",
                    criterion_scores=crit_payload,
                    missing_requirements=ev.missing_requirements,
                    evaluation_metadata=ev.evaluator_metadata,
                    ai_signal=ev.signals.ai_signal,
                    ai_score=ev.signals.ai_score,
                    similarity_score=ev.signals.similarity_score,
                )
                db.add(new_rev)

            # Record tamper-evident audit event for this evaluation
            evidence_refs = [
                {"reference_type": "sentence_offset", "identifier": f"crit_{c.criterion_key}", "location": f"{len(c.evidence_excerpts)} excerpts"}
                for c in ev.criterion_scores
            ]
            await append_audit_event(
                db=db,
                event_type="Submission Analyzed",
                target_type="submission",
                target_id=ev.submission_id,
                description=f"{ev.submission_id} · Rubric: {rubric.name} v{rubric.version} · Score: {ev.total_score}% · Evaluator: {req.evaluator_type}",
                actor_id=str(current_user.id),
                decision_rationale=f"Evaluated against rubric '{rubric.name}' with weighted total {ev.total_score}%",
                model_version=f"{req.evaluator_type}-v1.2",
                rubric_version=rubric.version,
                result_version="v1",
                uncertainty_status="supported" if not ev.is_incomplete else "inconclusive",
                evidence_references=evidence_refs,
                raw_metadata=ev.evaluator_metadata,
            )

    await db.commit()

    shortlist = rank_and_shortlist(evaluations)

    return APIResponse(
        data=BatchEvaluationResponse(
            rubric_id=rubric.id,
            rubric_name=rubric.name,
            evaluated_count=len(evaluations),
            evaluations=evaluations,
            shortlist=shortlist,
        ),
        message=f"Successfully evaluated {len(evaluations)} submissions against '{rubric.name}'.",
    )


# ── 4. Cohort Shortlist Endpoint ───────────────────────────────────────────────
@router.get(
    "/cohorts/{rubric_id}/shortlist",
    response_model=APIResponse[List[ShortlistedCandidateItem]],
    summary="Get ranked shortlist for a rubric cohort with tie breaking",
)
async def get_cohort_shortlist(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ShortlistedCandidateItem]]:
    rubric_res = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    rubric = rubric_res.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    reviews_res = await db.execute(
        sa.select(Review, Submission)
        .join(Submission, Review.submission_id == Submission.id)
        .where(Review.rubric_id == rubric_id)
    )
    pairs = reviews_res.all()

    evaluations: List[EvaluationResult] = []
    overrides_map: Dict[str, Dict[str, Any]] = {}

    for rev, sub in pairs:
        crit_scores = []
        if rev.criterion_scores:
            for c in rev.criterion_scores:
                crit_scores.append(CriterionEvaluation.model_validate(c))

        ev = EvaluationResult(
            submission_id=sub.id,
            submission_title=sub.title,
            rubric_id=rubric.id,
            rubric_name=rubric.name,
            rubric_version=rubric.version,
            total_score=rev.total_score,
            criterion_scores=crit_scores,
            missing_requirements=rev.missing_requirements or [],
            signals=DecoupledSignals(
                quality_score=rev.total_score,
                ai_signal=rev.ai_signal or "Low",
                ai_score=rev.ai_score or 0.0,
                similarity_score=rev.similarity_score or 0.0,
            ),
            evaluator_metadata=rev.evaluation_metadata or {},
        )
        evaluations.append(ev)
        overrides_map[sub.id] = {
            "status": rev.status,
            "override_flag": rev.override_flag,
            "override_reason": rev.override_reason,
            "total_score": rev.total_score,
        }

    shortlist = rank_and_shortlist(evaluations, status_overrides=overrides_map)
    return APIResponse(data=shortlist, message="Cohort shortlist retrieved")


# ── 5. Detailed Submission Evaluation Result ──────────────────────────────────
@router.get(
    "/results/{submission_id}",
    response_model=APIResponse[EvaluationResult],
    summary="Get full evaluation result, criterion excerpts, and decoupled signals for a submission",
)
async def get_submission_evaluation_result(
    submission_id: str,
    rubric_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvaluationResult]:
    query = sa.select(Review, Submission, Rubric).join(Submission, Review.submission_id == Submission.id).outerjoin(Rubric, Review.rubric_id == Rubric.id).where(Review.submission_id == submission_id)
    if rubric_id:
        query = query.where(Review.rubric_id == rubric_id)

    res = await db.execute(query)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No evaluation result found for submission '{submission_id}'.")

    rev, sub, rub = row
    crit_scores = []
    if rev.criterion_scores:
        for c in rev.criterion_scores:
            crit_scores.append(CriterionEvaluation.model_validate(c))

    ev = EvaluationResult(
        submission_id=sub.id,
        submission_title=sub.title,
        rubric_id=rub.id if rub else "",
        rubric_name=rub.name if rub else "Rubric",
        rubric_version=rub.version if rub else 1,
        total_score=rev.total_score,
        criterion_scores=crit_scores,
        missing_requirements=rev.missing_requirements or [],
        signals=DecoupledSignals(
            quality_score=rev.total_score,
            ai_signal=rev.ai_signal or "Low",
            ai_score=rev.ai_score or 0.0,
            similarity_score=rev.similarity_score or 0.0,
        ),
        evaluator_metadata=rev.evaluation_metadata or {},
    )
    return APIResponse(data=ev, message="Evaluation result retrieved")


# ── 6. Reviewer Override & Manual Adjustment ──────────────────────────────────
@router.post(
    "/reviews/{review_id}/override",
    response_model=APIResponse[ReviewRead],
    summary="Authorized reviewer manual score adjustment with mandatory rationale and audit logging",
)
async def override_review(
    review_id: str,
    req: ShortlistOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ReviewRead]:
    """
    Applies manual reviewer adjustment or status change.
    Requires non-empty override_reason for accountability and records an audit event.
    """
    res = await db.execute(sa.select(Review).where(Review.id == review_id))
    review = res.scalars().first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review '{review_id}' not found.")

    prev_status = review.status
    prev_score = review.total_score

    review.override_flag = True
    review.override_reason = req.override_reason
    if req.status:
        review.status = req.status
    if req.new_total_score is not None:
        review.total_score = req.new_total_score
    if req.notes:
        review.notes = req.notes

    # Append immutable audit event with hash chaining
    await append_audit_event(
        db=db,
        event_type="Override Recorded",
        target_type="review",
        target_id=review_id,
        description=f"Review {review_id} · Override: {prev_status} → {review.status} · Reason: {req.override_reason}",
        actor_id=str(current_user.id),
        decision_rationale=req.override_reason,
        uncertainty_status="supported",
        raw_metadata={
            "review_id": review_id,
            "previous_status": prev_status,
            "new_status": review.status,
            "previous_score": prev_score,
            "new_score": review.total_score,
            "override_reason": req.override_reason,
        },
    )

    await db.commit()
    await db.refresh(review)

    return APIResponse(data=ReviewRead.model_validate(review), message="Reviewer override applied and audit event logged.")


@router.patch("/submissions/{submission_id}/status")
async def update_submission_status(
    submission_id: str,
    update_req: StatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """Updates candidate status with optional reviewer override rationale (frontend compatibility)."""
    # Check if a review exists for this submission in DB
    rev_res = await db.execute(sa.select(Review).where(Review.submission_id == submission_id))
    rev = rev_res.scalars().first()
    if rev:
        rev.status = update_req.status
        if update_req.override_reason:
            rev.override_flag = True
            rev.override_reason = update_req.override_reason
        await db.commit()

    return APIResponse(
        data={"submission_id": submission_id, "new_status": update_req.status, "updated_by": current_user.email},
        message=f"Submission {submission_id} updated to {update_req.status}",
    )
