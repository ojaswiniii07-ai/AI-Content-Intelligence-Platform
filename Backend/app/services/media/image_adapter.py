"""
Image detector adapter — synthetic-image / AI-generation indicators.

Supports two backends (selected by IMAGE_DETECTOR env):
  - "hive"   : Hive Moderation API (requires HIVE_API_KEY)
  - "sightengine": SightEngine API (requires SIGHTENGINE_USER + SIGHTENGINE_SECRET)
  - unset / any other value → adapter reports not-configured; returns INCONCLUSIVE

Regions are ONLY populated when Hive returns bounding-box data in its response.
Scores from the provider are passed through verbatim — never adjusted or fabricated.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.services.media.base import (
    AdapterContext,
    BaseDetectorAdapter,
    DetectorResult,
    NotConfiguredError,
)


ADAPTER_KEY = "image_synthetic_v1"
MEDIA_TYPES = ["image"]


class ImageSyntheticAdapter(BaseDetectorAdapter):
    """
    Detects AI-generated / synthetically manipulated images.
    Uses Hive Moderation API if configured; SightEngine if configured;
    otherwise reports not configured and returns INCONCLUSIVE.
    """

    ADAPTER_KEY = ADAPTER_KEY
    MEDIA_TYPES = MEDIA_TYPES

    # When the detector explicitly returns bounding boxes, set to True.
    supports_regions = False  # Updated per backend below
    supports_frame_refs = False
    supports_time_ranges = False

    def __init__(self) -> None:
        self._backend = os.getenv("IMAGE_DETECTOR", "").lower()
        self._hive_key = os.getenv("HIVE_API_KEY", "")
        self._se_user = os.getenv("SIGHTENGINE_USER", "")
        self._se_secret = os.getenv("SIGHTENGINE_SECRET", "")

        if self._backend == "hive" and self._hive_key:
            self.supports_regions = True  # Hive returns bbox when it detects faces/regions

    def is_configured(self) -> bool:
        if self._backend == "hive":
            return bool(self._hive_key)
        if self._backend == "sightengine":
            return bool(self._se_user and self._se_secret)
        return False

    def analyze(self, ctx: AdapterContext) -> DetectorResult:
        if not self.is_configured():
            raise NotConfiguredError(f"Adapter {self.ADAPTER_KEY} is not configured.")

        if self._backend == "hive":
            return self._run_hive(ctx)
        if self._backend == "sightengine":
            return self._run_sightengine(ctx)

        raise NotConfiguredError(f"Unknown IMAGE_DETECTOR backend: {self._backend}")

    # ── Hive backend ──────────────────────────────────────────
    def _run_hive(self, ctx: AdapterContext) -> DetectorResult:
        """
        Calls Hive Moderation AI-image detection.
        Response fields used verbatim — no score adjustment.
        Bounding boxes only populated when present in Hive response.
        """
        try:
            import requests  # type: ignore
        except ImportError:
            raise NotConfiguredError("'requests' package is required for Hive adapter. pip install requests")

        with open(ctx.file_path, "rb") as f:
            files = {"image": (ctx.file_name, f, ctx.content_type)}
            resp = requests.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"token": self._hive_key},
                files=files,
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()

        # Parse Hive response — structure: {status:[{response:[{output:[{classes:[]}]}]}]}
        findings: List[Dict[str, Any]] = []
        ai_score: Optional[float] = None
        severity = "inconclusive"

        try:
            classes = data["status"][0]["response"][0]["output"][0]["classes"]
            for cls in classes:
                if cls.get("class") == "ai_generated":
                    ai_score = cls.get("score")
                    if ai_score is not None:
                        if ai_score >= 0.75:
                            severity = "high"
                        elif ai_score >= 0.45:
                            severity = "medium"
                        else:
                            severity = "low"
                    findings.append({
                        "indicator": "AI Generated Image",
                        "score": ai_score,
                        "explanation": (
                            f"Hive AI-generated image detector returned score {ai_score}. "
                            "Score is passed through verbatim from the Hive API."
                        ),
                        "region": None,  # Populate only if Hive returns bbox
                    })
        except (KeyError, IndexError, TypeError):
            # Unexpected response structure — return inconclusive
            findings.append({
                "indicator": "Parse Error",
                "explanation": "Unexpected response structure from Hive API. Result is inconclusive.",
            })

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="Hive AI-Image Detection",
            model_version="v2",
            provider="Hive Moderation",
            is_configured=True,
            score=ai_score,
            severity=severity,
            findings=findings,
            limitations=[
                "Score reflects probability of AI generation as computed by Hive v2.",
                "A high score is a decision-support signal, not proof of AI generation.",
                "Model has known accuracy limitations on certain artistic styles.",
            ],
            supports_regions=False,   # Hive /sync does not currently return region bbox
            supports_frame_refs=False,
            supports_time_ranges=False,
        )

    # ── SightEngine backend ───────────────────────────────────
    def _run_sightengine(self, ctx: AdapterContext) -> DetectorResult:
        """
        Calls SightEngine AI-generated image detector.
        Score from provider is passed through verbatim.
        SightEngine does not return bounding boxes for AI-gen detection.
        """
        try:
            import requests  # type: ignore
        except ImportError:
            raise NotConfiguredError("'requests' package is required for SightEngine adapter.")

        with open(ctx.file_path, "rb") as f:
            resp = requests.post(
                "https://api.sightengine.com/1.0/check.json",
                data={
                    "api_user": self._se_user,
                    "api_secret": self._se_secret,
                    "models": "genai",
                },
                files={"media": f},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()

        ai_score: Optional[float] = None
        severity = "inconclusive"
        findings: List[Dict[str, Any]] = []

        try:
            ai_score = data["type"]["ai_generated"]
            if ai_score is not None:
                if ai_score >= 0.75:
                    severity = "high"
                elif ai_score >= 0.40:
                    severity = "medium"
                else:
                    severity = "low"
            findings.append({
                "indicator": "AI Generated Image",
                "score": ai_score,
                "explanation": (
                    f"SightEngine genai model returned score {ai_score}. "
                    "Score is passed through verbatim."
                ),
            })
        except (KeyError, TypeError):
            findings.append({
                "indicator": "Parse Error",
                "explanation": "Unexpected SightEngine response. Result is inconclusive.",
            })

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="SightEngine GenAI",
            model_version="1.0",
            provider="SightEngine",
            is_configured=True,
            score=ai_score,
            severity=severity,
            findings=findings,
            limitations=[
                "SightEngine genai score reflects model confidence, not ground truth.",
                "No spatial localisation is returned — regions are not available.",
                "Results may vary for edited vs. fully generated images.",
            ],
            supports_regions=False,
            supports_frame_refs=False,
            supports_time_ranges=False,
        )
