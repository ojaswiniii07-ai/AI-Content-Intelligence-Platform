"""
Audio detector adapter — synthetic speech / manipulation indicators.

Supported backends (AUDIO_DETECTOR env var):
  - "elevenlabs_detect": ElevenLabs AI Speech Classifier (requires ELEVENLABS_API_KEY)
  - "hive_audio"       : Hive Audio AI Detection (requires HIVE_API_KEY)
  - unset              → not configured → INCONCLUSIVE returned

Time ranges are ONLY populated if the provider explicitly returns segment-level output.
ElevenLabs /v1/audio-classifier returns a single file-level probability — no time ranges.
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


class AudioSyntheticAdapter(BaseDetectorAdapter):
    ADAPTER_KEY = "audio_synthetic_v1"
    MEDIA_TYPES = ["audio", "video"]  # can analyze audio track from video too

    supports_regions = False
    supports_frame_refs = False
    supports_time_ranges = False  # updated per backend

    def __init__(self) -> None:
        self._backend = os.getenv("AUDIO_DETECTOR", "").lower()
        self._elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
        self._hive_key = os.getenv("HIVE_API_KEY", "")

        if self._backend == "hive_audio" and self._hive_key:
            self.supports_time_ranges = True  # Hive audio returns segment-level output

    def is_configured(self) -> bool:
        if self._backend == "elevenlabs_detect":
            return bool(self._elevenlabs_key)
        if self._backend == "hive_audio":
            return bool(self._hive_key)
        return False

    def analyze(self, ctx: AdapterContext) -> DetectorResult:
        if not self.is_configured():
            raise NotConfiguredError(f"Adapter {self.ADAPTER_KEY} is not configured.")

        if self._backend == "elevenlabs_detect":
            return self._run_elevenlabs(ctx)
        if self._backend == "hive_audio":
            return self._run_hive_audio(ctx)

        raise NotConfiguredError(f"Unknown AUDIO_DETECTOR backend: {self._backend}")

    # ── ElevenLabs backend ────────────────────────────────────
    def _run_elevenlabs(self, ctx: AdapterContext) -> DetectorResult:
        """
        ElevenLabs /v1/audio-classifier returns a single file-level probability.
        No time-range localisation available from this endpoint.
        """
        try:
            import requests  # type: ignore
        except ImportError:
            raise NotConfiguredError("'requests' package required. pip install requests")

        with open(ctx.file_path, "rb") as f:
            resp = requests.post(
                "https://api.elevenlabs.io/v1/audio-classifier",
                headers={"xi-api-key": self._elevenlabs_key},
                files={"audio": (ctx.file_name, f, ctx.content_type)},
                timeout=60,
            )
        resp.raise_for_status()
        data = resp.json()

        ai_score: Optional[float] = None
        severity = "inconclusive"
        findings: List[Dict[str, Any]] = []

        try:
            ai_score = float(data.get("ai_speech_probability", data.get("probability", None)))
            if ai_score is not None:
                severity = "high" if ai_score >= 0.75 else "medium" if ai_score >= 0.40 else "low"
            findings.append({
                "indicator": "AI Synthetic Speech",
                "score": ai_score,
                "time_ranges": None,  # NOT available from this endpoint
                "explanation": (
                    f"ElevenLabs audio classifier returned probability {ai_score}. "
                    "This is a file-level estimate — no time-range localisation is available."
                ),
            })
        except (TypeError, ValueError, KeyError):
            findings.append({"indicator": "Parse Error", "explanation": "Unexpected ElevenLabs response."})

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="ElevenLabs Audio Classifier",
            model_version="v1",
            provider="ElevenLabs",
            is_configured=True,
            score=ai_score,
            severity=severity,
            findings=findings,
            limitations=[
                "File-level probability only — no time-range or segment localisation.",
                "Short clips (<3s) may produce less reliable estimates.",
                "Score is a probabilistic signal, not proof of synthetic origin.",
            ],
            supports_time_ranges=False,
        )

    # ── Hive audio backend ────────────────────────────────────
    def _run_hive_audio(self, ctx: AdapterContext) -> DetectorResult:
        """
        Hive audio AI detection.
        If Hive returns segment-level results, time_ranges are populated verbatim.
        """
        try:
            import requests  # type: ignore
        except ImportError:
            raise NotConfiguredError("'requests' package required. pip install requests")

        with open(ctx.file_path, "rb") as f:
            resp = requests.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"token": self._hive_key},
                files={"audio": (ctx.file_name, f, ctx.content_type)},
                timeout=120,
            )
        resp.raise_for_status()
        data = resp.json()

        ai_score: Optional[float] = None
        severity = "inconclusive"
        findings: List[Dict[str, Any]] = []
        time_ranges: Optional[List[Dict[str, float]]] = None

        try:
            classes = data["status"][0]["response"][0]["output"][0]["classes"]
            segments = data["status"][0]["response"][0].get("segments", [])

            for cls in classes:
                if cls.get("class") == "ai_generated":
                    ai_score = cls.get("score")
                    if ai_score is not None:
                        severity = "high" if ai_score >= 0.75 else "medium" if ai_score >= 0.40 else "low"

            # Populate time_ranges only when Hive segment data is present
            if segments:
                time_ranges = [
                    {"start_sec": s.get("start_time_ms", 0) / 1000, "end_sec": s.get("end_time_ms", 0) / 1000}
                    for s in segments if s.get("class") == "ai_generated"
                ]

            findings.append({
                "indicator": "AI Synthetic Speech",
                "score": ai_score,
                "time_ranges": time_ranges,
                "explanation": (
                    f"Hive audio AI detection score: {ai_score}. "
                    f"{'Time-range localisation available.' if time_ranges else 'No segment data returned.'}"
                ),
            })
        except (KeyError, IndexError, TypeError):
            findings.append({"indicator": "Parse Error", "explanation": "Unexpected Hive audio response."})

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="Hive Audio AI Detection",
            model_version="v2",
            provider="Hive Moderation",
            is_configured=True,
            score=ai_score,
            severity=severity,
            findings=findings,
            limitations=[
                "Time ranges are only populated when Hive returns segment-level data.",
                "Score and segments are verbatim from Hive — no post-processing adjustments.",
                "Background music or compression artifacts can affect accuracy.",
            ],
            supports_time_ranges=bool(time_ranges),
        )
