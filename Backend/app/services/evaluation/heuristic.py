from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.review import (
    CriterionEvaluation,
    DecoupledSignals,
    EvaluationResult,
    StyleEvaluation,
)
from app.services.evaluation.base import BaseEvaluator


class HeuristicRuleEvaluator(BaseEvaluator):
    """
    Deterministic rule-based rubric evaluator.
    Analyzes content depth, keyword benchmarks, argument coherence,
    and style compliance. Always available (does not require external LLM).
    """

    @property
    def name(self) -> str:
        return "heuristic_rule_evaluator"

    @property
    def version(self) -> str:
        return "v1.2.0"

    def is_configured(self) -> bool:
        return True

    async def evaluate(
        self,
        submission_id: str,
        submission_title: str,
        submission_text: str,
        rubric_data: Dict[str, Any],
        ai_context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        start_time = time.perf_counter()
        clean_text = (submission_text or "").strip()
        words = clean_text.split()
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if len(s.strip()) > 5]

        # Check for incomplete submission
        is_incomplete = word_count < 25 or len(clean_text) == 0

        criteria = rubric_data.get("criteria", [])
        if not criteria and "weights" in rubric_data:
            # Fallback default criteria from weights dict
            criteria = [
                {"key": k, "title": k.capitalize(), "description": f"Evaluation of {k}", "weight": v, "min_score": 0.0, "max_score": 10.0, "required": True}
                for k, v in rubric_data["weights"].items()
            ]

        criterion_evaluations: List[CriterionEvaluation] = []
        all_missing_requirements: List[str] = []
        total_weighted_points = 0.0

        for crit in criteria:
            c_key = crit.get("key", "criterion")
            c_title = crit.get("title", c_key.capitalize())
            c_desc = crit.get("description", "")
            c_weight = float(crit.get("weight", 0.33))
            c_min = float(crit.get("min_score", 0.0))
            c_max = float(crit.get("max_score", 10.0))
            benchmarks = crit.get("benchmarks", [])

            excerpts: List[str] = []
            missing_for_crit: List[str] = []

            if is_incomplete:
                score = c_min
                explanation = f"Submission is incomplete or lacks substantive content ({word_count} words). Cannot adequately evaluate {c_title}."
                missing_for_crit.append(f"Substantive exposition addressing {c_title}")
            else:
                # Find matching sentences based on keywords from key, title, and description
                keywords = set(re.findall(r"\w{4,}", (c_key + " " + c_title + " " + c_desc).lower()))
                matched_sentences = []
                for s in sentences:
                    s_lower = s.lower()
                    overlap = sum(1 for kw in keywords if kw in s_lower)
                    if overlap > 0:
                        matched_sentences.append((overlap, s))

                matched_sentences.sort(key=lambda x: x[0], reverse=True)
                excerpts = [s for _, s in matched_sentences[:2]]
                if not excerpts and sentences:
                    # Provide first representative sentence
                    excerpts = [sentences[0]]

                # Benchmark check
                benchmark_hits = 0
                if benchmarks:
                    for bm in benchmarks:
                        if bm.lower() in clean_text.lower():
                            benchmark_hits += 1
                        else:
                            missing_for_crit.append(f"Missing benchmark requirement: '{bm}'")

                # Content depth scoring factors
                depth_ratio = min(1.0, word_count / 150.0)
                relevance_ratio = min(1.0, len(matched_sentences) / 2.0) if matched_sentences else 0.4
                benchmark_ratio = (benchmark_hits / len(benchmarks)) if benchmarks else 0.85

                raw_pct = (depth_ratio * 0.4) + (relevance_ratio * 0.4) + (benchmark_ratio * 0.2)
                score = round(c_min + raw_pct * (c_max - c_min), 1)
                score = max(c_min, min(c_max, score))

                if score >= (c_max * 0.85):
                    explanation = f"Strong evidence addressing {c_title}. Clear argumentation and thorough coverage."
                elif score >= (c_max * 0.65):
                    explanation = f"Satisfactory coverage of {c_title}. Core concepts articulated with moderate elaboration."
                else:
                    explanation = f"Partial coverage of {c_title}. Arguments would benefit from additional substantiation and concrete examples."

            # Weighted score contribution on a 0-100 scale: (score / c_max) * (c_weight * 100)
            score_normalized = (score / c_max) if c_max > 0 else 0.0
            weighted_score = round(score_normalized * (c_weight * 100.0), 2)
            total_weighted_points += weighted_score

            all_missing_requirements.extend(missing_for_crit)

            criterion_evaluations.append(
                CriterionEvaluation(
                    criterion_key=c_key,
                    criterion_title=c_title,
                    score=score,
                    max_score=c_max,
                    weight=c_weight,
                    weighted_score=weighted_score,
                    evidence_excerpts=excerpts,
                    explanation=explanation,
                    missing_requirements=missing_for_crit,
                )
            )

        # Style rule evaluation
        style_rules = rubric_data.get("style_rules") or {}
        style_violations: List[str] = []
        style_score = 10.0

        if style_rules:
            min_w = style_rules.get("min_words")
            max_w = style_rules.get("max_words")
            req_sections = style_rules.get("required_sections") or []
            forbidden = style_rules.get("forbidden_phrases") or []

            if min_w and word_count < min_w:
                style_violations.append(f"Word count ({word_count}) below minimum required ({min_w})")
                style_score -= 2.5
            if max_w and word_count > max_w:
                style_violations.append(f"Word count ({word_count}) exceeds maximum allowed ({max_w})")
                style_score -= 2.0
            for sec in req_sections:
                if sec.lower() not in clean_text.lower():
                    style_violations.append(f"Required section '{sec}' not detected")
                    style_score -= 2.0
            for phrase in forbidden:
                if phrase.lower() in clean_text.lower():
                    style_violations.append(f"Contains prohibited phrasing: '{phrase}'")
                    style_score -= 3.0

        style_score = max(0.0, min(10.0, style_score))
        style_eval = StyleEvaluation(
            score=round(style_score, 1),
            passed=len(style_violations) == 0,
            word_count=word_count,
            violations=style_violations,
            observations="All style requirements met." if not style_violations else "; ".join(style_violations),
        )

        final_total = round(max(0.0, min(100.0, total_weighted_points)), 1)

        # Decouple AI signals: read purely as informational metadata
        ai_ctx = ai_context or {}
        ai_signal = ai_ctx.get("ai_signal", "Low")
        ai_score = float(ai_ctx.get("ai_score", 0.0))
        sim_score = float(ai_ctx.get("similarity_score", 0.0))

        signals = DecoupledSignals(
            quality_score=final_total,
            rubric_compliance="Full" if not all_missing_requirements else "Partial",
            ai_signal=ai_signal,
            ai_score=ai_score,
            similarity_score=sim_score,
            decoupling_note=(
                f"Quality total ({final_total}%) is calculated independently from the AI signal "
                f"({ai_signal}, {ai_score}%) and similarity ({sim_score}%)."
            ),
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return EvaluationResult(
            submission_id=submission_id,
            submission_title=submission_title,
            rubric_id=str(rubric_data.get("id", "preview_rubric")),
            rubric_name=rubric_data.get("name", "Rubric"),
            rubric_version=rubric_data.get("version", 1),
            total_score=final_total,
            criterion_scores=criterion_evaluations,
            style_evaluation=style_eval,
            missing_requirements=all_missing_requirements,
            signals=signals,
            evaluator_metadata={
                "evaluator_type": self.name,
                "evaluator_version": self.version,
                "execution_time_ms": elapsed_ms,
                "word_count": word_count,
            },
            evaluated_at=datetime.now(timezone.utc),
            is_incomplete=is_incomplete,
        )
