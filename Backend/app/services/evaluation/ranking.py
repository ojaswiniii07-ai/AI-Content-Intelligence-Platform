from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.schemas.review import EvaluationResult, ShortlistedCandidateItem


def rank_and_shortlist(
    evaluations: List[EvaluationResult],
    status_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    priority_criterion_key: Optional[str] = "reasoning",
) -> List[ShortlistedCandidateItem]:
    """
    Ranks evaluation results and produces a shortlisted cohort with explicit tie handling.

    Tie-breaking cascade:
      1. Primary: total_score descending
      2. Tie-break 1: priority criterion score (e.g. 'reasoning' or 'relevance')
      3. Tie-break 2: missing requirements count (fewer is superior)
      4. Tie-break 3: style compliance score
      5. Tie-break 4: deterministic by submission_id
    """
    status_overrides = status_overrides or {}

    def get_criterion_score(ev: EvaluationResult, key: str) -> float:
        for c in ev.criterion_scores:
            if c.criterion_key.lower() == key.lower():
                return c.score
        # Fallback to first criterion if key not found
        return ev.criterion_scores[0].score if ev.criterion_scores else 0.0

    def get_style_score(ev: EvaluationResult) -> float:
        if ev.style_evaluation:
            return ev.style_evaluation.score
        return 10.0

    # Group and detect ties
    def sort_key(ev: EvaluationResult):
        # Python sort is ascending; use negative for descending
        p_score = get_criterion_score(ev, priority_criterion_key or "reasoning")
        missing_count = len(ev.missing_requirements)
        style_sc = get_style_score(ev)
        return (
            -ev.total_score,
            -p_score,
            missing_count,  # lower count is better
            -style_sc,
            ev.submission_id,
        )

    sorted_evals = sorted(evaluations, key=sort_key)

    candidates: List[ShortlistedCandidateItem] = []

    for idx, ev in enumerate(sorted_evals):
        rank_str = f"#{idx + 1}"
        tie_broken = False
        tie_break_reason = None

        # Check for tie with preceding or succeeding neighbor
        neighbors = []
        if idx > 0:
            neighbors.append(sorted_evals[idx - 1])
        if idx < len(sorted_evals) - 1:
            neighbors.append(sorted_evals[idx + 1])

        for neighbor in neighbors:
            if abs(ev.total_score - neighbor.total_score) < 0.001:
                tie_broken = True
                p_self = get_criterion_score(ev, priority_criterion_key or "reasoning")
                p_other = get_criterion_score(neighbor, priority_criterion_key or "reasoning")
                if abs(p_self - p_other) > 0.001:
                    tie_break_reason = f"Tied at {ev.total_score}%; broke tie via {priority_criterion_key} score ({p_self} vs {p_other})"
                elif len(ev.missing_requirements) != len(neighbor.missing_requirements):
                    tie_break_reason = f"Tied at {ev.total_score}%; broke tie via missing requirements count ({len(ev.missing_requirements)} vs {len(neighbor.missing_requirements)})"
                else:
                    tie_break_reason = f"Tied at {ev.total_score}%; broke tie via style compliance score"
                break

        # Map per-criterion scores
        relevance_sc = get_criterion_score(ev, "relevance")
        reasoning_sc = get_criterion_score(ev, "reasoning")
        originality_sc = get_criterion_score(ev, "originality")

        crit_breakdown = {c.criterion_key: c.score for c in ev.criterion_scores}

        # Check existing override if any
        override_info = status_overrides.get(ev.submission_id, {})
        status = override_info.get("status")
        if not status:
            if ev.is_incomplete:
                status = "flagged"
            elif ev.total_score >= 80.0:
                status = "shortlisted"
            elif ev.total_score >= 65.0:
                status = "pending"
            else:
                status = "pending"

        override_flag = override_info.get("override_flag", False)
        override_reason = override_info.get("override_reason")
        adjusted_total = override_info.get("total_score", ev.total_score)

        # Summary text
        summary = ""
        if ev.criterion_scores:
            summary = ev.criterion_scores[0].explanation
            if len(ev.criterion_scores) > 1 and len(summary) < 80:
                summary += " " + ev.criterion_scores[1].explanation

        candidates.append(
            ShortlistedCandidateItem(
                id=ev.submission_id,
                rank=rank_str,
                name=ev.submission_title,
                relevance=relevance_sc,
                reasoning=reasoning_sc,
                originality=originality_sc,
                total=adjusted_total,
                ai_signal=ev.signals.ai_signal,
                ai_score=ev.signals.ai_score,
                status=status,
                summary=summary,
                criterion_breakdown=crit_breakdown,
                is_incomplete=ev.is_incomplete,
                missing_requirements_count=len(ev.missing_requirements),
                tie_broken=tie_broken,
                tie_break_reason=tie_break_reason,
                override_flag=override_flag,
                override_reason=override_reason,
                similarity_score=ev.signals.similarity_score,
                criterion_scores=[c.model_dump() for c in ev.criterion_scores],
                evaluator_metadata=ev.evaluator_metadata,
                missing_requirements=ev.missing_requirements,
            )
        )

    return candidates
