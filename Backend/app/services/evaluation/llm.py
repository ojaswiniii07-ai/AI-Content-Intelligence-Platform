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
        self._api_key = api_key or getattr(settings, "LLM_EVALUATOR_API_KEY", "") or getattr(settings, "OPENROUTER_API_KEY", "")
        self._provider = provider or getattr(settings, "LLM_EVALUATOR_PROVIDER", "openai")
        if not provider and self._api_key.startswith("sk-or-"):
            self._provider = "openrouter"
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
            "Evaluate the provided submission text against the rubric criteria.\n\n"
            "CRITICAL DECOUPLING DIRECTIVE:\n"
            "1. Evaluate purely on the content, argument quality, and rubric criteria.\n"
            "2. Never lower a score solely due to an AI detector flag or similarity indicators.\n"
            "3. For each criterion in the rubric, assign an objective numeric score within [0, max_score] (typically 0-10).\n"
            "4. Provide exact evidence excerpts from the submission, an insightful analytical explanation, and a list of any missing requirements.\n\n"
            "You MUST return valid JSON in the following exact format:\n"
            "{\n"
            '  "criteria": {\n'
            '    "<criterion_key>": {\n'
            '      "score": 8.5,\n'
            '      "evidence_excerpts": ["excerpt quote 1"],\n'
            '      "explanation": "Clear explanation of how the submission meets or falls short of this criterion.",\n'
            '      "missing_requirements": ["optional missing item"]\n'
            '    }\n'
            '  }\n'
            "}\n"
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

        if self._provider == "openrouter" or self._api_key.startswith("sk-or-"):
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            headers["HTTP-Referer"] = "https://authentiq.ai"
            headers["X-Title"] = "AuthentiQ"
            if "/" not in payload["model"]:
                payload["model"] = f"openai/{payload['model']}"
            # Provide graceful fallbacks in case primary model is temporarily rate-limited upstream
            payload["models"] = [
                self._model,
                "nvidia/nemotron-3.5-lightning:free",
                "recursive/flint-v1.0:free",
            ]
        else:
            api_url = "https://api.openai.com/v1/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                res = await client.post(api_url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
        except httpx.TimeoutException as te:
            raise EvaluatorUnavailableError(f"LLM evaluator timed out after {self._timeout}s: {te}")
        except Exception as e:
            raise EvaluatorUnavailableError(f"LLM evaluator request failed: {e}")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        raw_json_str = data["choices"][0]["message"]["content"].strip()
        
        # Robust JSON cleaning: handle code blocks or trailing text
        cleaned_json = raw_json_str
        if "```json" in cleaned_json:
            cleaned_json = cleaned_json.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned_json:
            cleaned_json = cleaned_json.split("```", 1)[1].split("```", 1)[0].strip()
        elif not cleaned_json.startswith("{") and "{" in cleaned_json:
            start_idx = cleaned_json.find("{")
            end_idx = cleaned_json.rfind("}")
            if end_idx > start_idx:
                cleaned_json = cleaned_json[start_idx:end_idx+1]

        try:
            parsed = json.loads(cleaned_json)
        except Exception as err:
            raise EvaluatorUnavailableError(f"Failed to parse LLM evaluation JSON: {err}. Raw output: {raw_json_str[:200]}")

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

        crit_weights = rubric_data.get("weights") or {}
        crit_map = {c.get("key", c.get("id")): c for c in criteria if isinstance(c, dict)}

        for c_key, c_val in parsed_items:
            spec = crit_map.get(c_key, {})
            # Determine weight
            c_weight = float(
                spec.get("weight")
                or crit_weights.get(c_key)
                or (1.0 / max(1, len(parsed_items)))
            )
            # Determine max scale
            c_max = float(
                spec.get("max_score")
                or spec.get("scale_max")
                or rubric_data.get("scoring_scale")
                or 10.0
            )
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
                    criterion_title=spec.get("title") or spec.get("name") or c_key.replace("_", " ").title(),
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
