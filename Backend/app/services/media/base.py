"""
Base adapter interface for all media analysis detectors.

Rules enforced by this interface:
- is_configured() MUST return False when required credentials/models are absent.
- analyze() MUST raise NotConfiguredError when not configured.
- Temporal fields (timestamps, frame refs, regions) MUST be None unless the
  underlying model explicitly supports spatial/temporal localisation.
- NEVER fabricate scores, regions, timestamps, or percentages.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class NotConfiguredError(RuntimeError):
    """Raised when a detector adapter is called but not properly configured."""


@dataclass
class AdapterContext:
    """Immutable context passed into every adapter.analyze() call."""
    file_path: str          # Absolute path to the temp file on disk
    file_name: str
    content_type: str
    file_size_bytes: int
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectorResult:
    """
    Canonical output from any detector adapter.
    Temporal / spatial fields default to None — adapters MUST NOT set them
    unless the underlying model explicitly produces such output.
    """
    adapter_key: str
    model_name: str
    model_version: str
    provider: str
    is_configured: bool
    score: Optional[float]                     # 0-1 or None = inconclusive
    severity: str                              # low | medium | high | inconclusive
    findings: List[Dict[str, Any]]             # List of raw finding dicts
    limitations: List[str]
    skip_reason: Optional[str] = None          # Set when is_configured=False

    # Spatial / temporal — only set by adapters that truly support them
    supports_regions: bool = False
    supports_frame_refs: bool = False
    supports_time_ranges: bool = False


class BaseDetectorAdapter(ABC):
    """Abstract base for all media detector adapters."""

    ADAPTER_KEY: str          # unique string identifier, e.g. "hive_image_v1"
    MEDIA_TYPES: List[str]    # ["image"] | ["audio"] | ["video"] | ["audio","video"]

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True only when ALL required env vars / model files are present."""

    @abstractmethod
    def analyze(self, ctx: AdapterContext) -> DetectorResult:
        """
        Run inference. MUST raise NotConfiguredError if is_configured() is False.
        MUST NOT fabricate any score, region, or timestamp.
        """

    def safe_analyze(self, ctx: AdapterContext) -> DetectorResult:
        """
        Wrapper that returns a safe INCONCLUSIVE result instead of raising
        when the adapter is not configured. The router uses this method.
        """
        if not self.is_configured():
            return DetectorResult(
                adapter_key=self.ADAPTER_KEY,
                model_name="N/A",
                model_version="N/A",
                provider="N/A",
                is_configured=False,
                score=None,
                severity="inconclusive",
                findings=[],
                limitations=[f"Adapter '{self.ADAPTER_KEY}' is not configured — required keys are missing."],
                skip_reason=f"Adapter '{self.ADAPTER_KEY}' requires configuration. See .env.example.",
            )
        return self.analyze(ctx)
