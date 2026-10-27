from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.schemas.review import EvaluationResult


class EvaluatorUnavailableError(Exception):
    """Raised when an evaluator is requested but unconfigured or offline."""
    pass


class BaseEvaluator(ABC):
    """Abstract base class for all rubric response evaluators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the evaluator."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Version string of the evaluator/prompt."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if required API keys / services are available."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        submission_id: str,
        submission_title: str,
        submission_text: str,
        rubric_data: Dict[str, Any],
        ai_context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a single submission text against a rubric.

        Decoupling Rule:
          `ai_context` is provided solely for informational reporting in the output.
          It must NEVER lower the score or trigger automated rejections.
        """
        pass
