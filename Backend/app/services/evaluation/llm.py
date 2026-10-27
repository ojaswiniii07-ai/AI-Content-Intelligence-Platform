from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.schemas.review import (
    CriterionEvaluation,
    DecoupledSignals,
    EvaluationResult,
    StyleEvaluation,
)
from app.services.evaluation.base import BaseEvaluator, EvaluatorUnavailableError

RUBRIC_EVAL_PROMPT_VERSION = "rubric_eval_v2.1"


class LLMEvaluator(BaseEvaluator):
    """
    LLM-powered rubric evaluator.
    Uses versioned prompts, strict JSON schema output, timeouts,
    and metadata persistence.

    Honesty Contract:
      If not configured (missing API key or provider), raises
      EvaluatorUnavailableError. Never fabricates fake scores.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self._api_key = api_key or getattr(settings, "LLM_EVALUATOR_API_KEY", "")
        self._provider = provider or getattr(settings, "LLM_EVALUATOR_PROVIDER", "openai")
        self._model = model or getattr(settings, "LLM_EVALUATOR_MODEL", "gpt-4o")
        self._timeout = timeout_seconds or getattr(settings, "LLM_EVALUATOR_TIMEOUT_SECONDS", 30)

    @property
    def name(self) -> str:
        return "llm_evaluator"

    @property
    def version(self) -> str:
        return RUBRIC_EVAL_PROMPT_VERSION

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    async def evaluate(
        self,
        submission_id: str,
        submission_title: str,
        submission_text: str,
        rubric_data: Dict[str, Any],
        ai_context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        if not self.is_configured():
            raise EvaluatorUnavailableError(
                "LLM evaluator is not configured. Missing LLM_EVALUATOR_API_KEY. "
                "Per system safety policy, synthetic or fabricated scores will not be returned."
            )

        start_time = time.perf_counter()
        criteria = rubric_data.get("criteria", [])
        style_rules = rubric_data.get("style_rules", {})

        system_prompt = (
            "You are an expert, objective rubric evaluation engine. "
            "Evaluate the provided submission text against the rubric criteria.\n"
            "CRITICAL DECOUPLING DIRECTIVE:\n"
            "1. Evaluate purely on the content, argument quality, and rubric criteria.\n"
            "2. Never lower a score solely due to an AI detector flag or similarity indicators.\n"
            "3. For each criterion, provide a numeric score within the specified [min_score, max_score] range, "
            "exact evidence quotes from the submission, an explanation, and any missing requirements.\n"
            "Return valid JSON matching the specified schema."
        )

        user_content = {
            "submission_title": submission_title,
            "submission_text": submission_text,
            "rubric_name": rubric_data.get("name", "Evaluation Rubric"),
            "criteria": criteria,
            "style_rules": style_rules,
        }

        # Call OpenAI / compatible endpoint with timeout
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
        except httpx.TimeoutException as te:
            raise EvaluatorUnavailableError(f"LLM evaluator timed out after {self._timeout}s: {te}")
        except Exception as e:
            raise EvaluatorUnavailableError(f"LLM evaluator request failed: {e}")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        raw_json_str = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_json_str)

        # Build CriterionEvaluation list
        criterion_evaluations: List[CriterionEvaluation] = []
        total_weighted = 0.0
        all_missing = []

        parsed_criteria = parsed.get("criteria", {})
        # Can be dict of key -> obj or list of objs
        if isinstance(parsed_criteria, dict):
            parsed_items = parsed_criteria.items()
        elif isinstance(parsed_criteria, list):
            parsed_items = [(c.get("key", f"crit_{i}"), c) for i, c in enumerate(parsed_criteria)]
        else:
            parsed_items = []

        crit_map = {c.get("key"): c for c in criteria}

        for c_key, c_val in parsed_items:
            spec = crit_map.get(c_key, {})
            c_weight = float(spec.get("weight", 0.33))
            c_max = float(spec.get("max_score", 10.0))
            score = float(c_val.get("score", 0.0))
            excerpts = c_val.get("evidence_excerpts", [])
            explanation = c_val.get("explanation", "")
            missing = c_val.get("missing_requirements", [])

            weighted_score = round((score / c_max if c_max > 0 else 0.0) * (c_weight * 100.0), 2)
            total_weighted += weighted_score
            all_missing.extend(missing)

            criterion_evaluations.append(
                CriterionEvaluation(
                    criterion_key=c_key,
                    criterion_title=spec.get("title", c_key),
                    score=score,
                    max_score=c_max,
                    weight=c_weight,
                    weighted_score=weighted_score,
                    evidence_excerpts=excerpts,
                    explanation=explanation,
                    missing_requirements=missing,
                )
            )

        final_total = round(max(0.0, min(100.0, total_weighted)), 1)
        ai_ctx = ai_context or {}
        ai_signal = ai_ctx.get("ai_signal", "Low")
        ai_score = float(ai_ctx.get("ai_score", 0.0))
        sim_score = float(ai_ctx.get("similarity_score", 0.0))

        signals = DecoupledSignals(
            quality_score=final_total,
            rubric_compliance="Full" if not all_missing else "Partial",
            ai_signal=ai_signal,
            ai_score=ai_score,
            similarity_score=sim_score,
            decoupling_note="Quality total is derived exclusively from rubric criteria. AI flags and similarity signals are non-penalizing.",
        )

        return EvaluationResult(
            submission_id=submission_id,
            submission_title=submission_title,
            rubric_id=str(rubric_data.get("id", "llm_rubric")),
            rubric_name=rubric_data.get("name", "Rubric"),
            rubric_version=rubric_data.get("version", 1),
            total_score=final_total,
            criterion_scores=criterion_evaluations,
            style_evaluation=None,
            missing_requirements=all_missing,
            signals=signals,
            evaluator_metadata={
                "evaluator_type": self.name,
                "evaluator_version": self.version,
                "model": self._model,
                "prompt_version": RUBRIC_EVAL_PROMPT_VERSION,
                "execution_time_ms": elapsed_ms,
                "tokens_used": data.get("usage", {}),
            },
            evaluated_at=datetime.now(timezone.utc),
            is_incomplete=False,
        )
