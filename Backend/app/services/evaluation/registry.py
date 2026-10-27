from __future__ import annotations

from typing import Dict
from app.services.evaluation.base import BaseEvaluator
from app.services.evaluation.heuristic import HeuristicRuleEvaluator
from app.services.evaluation.llm import LLMEvaluator

_EVALUATORS: Dict[str, BaseEvaluator] = {
    "heuristic": HeuristicRuleEvaluator(),
    "llm": LLMEvaluator(),
}


def get_evaluator(evaluator_type: str = "heuristic") -> BaseEvaluator:
    """Retrieve registered evaluator by key ('heuristic' or 'llm')."""
    evaluator = _EVALUATORS.get(evaluator_type.lower())
    if not evaluator:
        raise ValueError(f"Unknown evaluator type: '{evaluator_type}'. Available: {list(_EVALUATORS.keys())}")
    return evaluator


def register_evaluator(name: str, evaluator: BaseEvaluator) -> None:
    """Register custom evaluator implementation."""
    _EVALUATORS[name.lower()] = evaluator
