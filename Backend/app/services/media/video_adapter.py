"""
Video detector adapter — manipulation and sampled-frame analysis.

Supported backends (VIDEO_DETECTOR env var):
  - "hive_video"    : Hive Video Deepfake Detection (requires HIVE_API_KEY)
  - "microsoft_video": Azure Video Indexer (requires AZURE_VIDEO_INDEXER_KEY + AZURE_VIDEO_INDEXER_ACCOUNT_ID)
  - unset           → not configured → INCONCLUSIVE

Frame references and timestamps are ONLY populated when the provider
returns frame-level or clip-level output. Never fabricated.

Optional AV-consistency check is ONLY run when:
  - The video has an audio track (has_audio_track=True in metadata)
  - AV_CONSISTENCY_CHECK env var is "true"
  - At least one audio adapter is configured
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


class VideoManipulationAdapter(BaseDetectorAdapter):
    ADAPTER_KEY = "video_manipulation_v1"
    MEDIA_TYPES = ["video"]

    supports_regions = False
    supports_frame_refs = False   # set True if provider returns frame-level output
    supports_time_ranges = False

    def __init__(self) -> None:
        self._backend = os.getenv("VIDEO_DETECTOR", "").lower()
        self._hive_key = os.getenv("HIVE_API_KEY", "")
        self._azure_key = os.getenv("AZURE_VIDEO_INDEXER_KEY", "")
        self._azure_account = os.getenv("AZURE_VIDEO_INDEXER_ACCOUNT_ID", "")
        self._azure_location = os.getenv("AZURE_VIDEO_INDEXER_LOCATION", "trial")

        if self._backend in ("hive_video", "microsoft_video"):
            self.supports_frame_refs = True  # Both return clip/frame data

    def is_configured(self) -> bool:
        if self._backend == "hive_video":
            return bool(self._hive_key)
        if self._backend == "microsoft_video":
            return bool(self._azure_key and self._azure_account)
        return False

    def analyze(self, ctx: AdapterContext) -> DetectorResult:
        if not self.is_configured():
            raise NotConfiguredError(f"Adapter {self.ADAPTER_KEY} is not configured.")

        if self._backend == "hive_video":
            return self._run_hive_video(ctx)
        if self._backend == "microsoft_video":
            return self._run_azure_video(ctx)

        raise NotConfiguredError(f"Unknown VIDEO_DETECTOR backend: {self._backend}")

    # ── Hive Video backend ────────────────────────────────────
    def _run_hive_video(self, ctx: AdapterContext) -> DetectorResult:
        """Hive video deepfake detection with segment-level output."""
        try:
            import requests  # type: ignore
        except ImportError:
            raise NotConfiguredError("'requests' package required. pip install requests")

        with open(ctx.file_path, "rb") as f:
            resp = requests.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"token": self._hive_key},
                files={"video": (ctx.file_name, f, ctx.content_type)},
                timeout=300,
            )
        resp.raise_for_status()
        data = resp.json()

        ai_score: Optional[float] = None
        severity = "inconclusive"
        findings: List[Dict[str, Any]] = []
        frame_refs: Optional[List[Dict[str, Any]]] = None

        try:
            outputs = data["status"][0]["response"][0]["output"]
            frame_refs_raw = []
            for out in outputs:
                for cls in out.get("classes", []):
                    if cls.get("class") == "deepfake":
                        clip_score = cls.get("score")
                        if clip_score is not None:
                            if ai_score is None or clip_score > ai_score:
                                ai_score = clip_score
                            ts = out.get("time", {})
                            frame_refs_raw.append({
                                "timestamp_sec": ts.get("start", None),
                                "end_sec": ts.get("end", None),
                                "score": clip_score,
                            })

            if ai_score is not None:
                severity = "high" if ai_score >= 0.70 else "medium" if ai_score >= 0.40 else "low"

            # Only assign frame_refs when provider actually returned them
            if frame_refs_raw:
                frame_refs = frame_refs_raw

            findings.append({
                "indicator": "Video Deepfake / Manipulation",
                "score": ai_score,
                "frame_references": frame_refs,
                "explanation": (
                    f"Hive video deepfake detection peak score: {ai_score}. "
                    f"{'Clip-level timestamps available.' if frame_refs else 'No clip-level data returned.'}"
                ),
            })
        except (KeyError, IndexError, TypeError):
            findings.append({"indicator": "Parse Error", "explanation": "Unexpected Hive video response."})

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="Hive Video Deepfake Detection",
            model_version="v2",
            provider="Hive Moderation",
            is_configured=True,
            score=ai_score,
            severity=severity,
            findings=findings,
            limitations=[
                "Score is peak clip probability — individual frames may vary significantly.",
                "Frame/timestamp references only available when Hive returns clip-level output.",
                "Compressed or low-resolution video reduces detection reliability.",
                "Score is a probabilistic indicator, not proof of deepfake.",
            ],
            supports_frame_refs=bool(frame_refs),
            supports_time_ranges=bool(frame_refs),
        )

    # ── Azure Video Indexer backend ───────────────────────────
    def _run_azure_video(self, ctx: AdapterContext) -> DetectorResult:
        """
        Azure Video Indexer — uploads video, polls for analysis, extracts insights.
        Frame-level face detection and emotion changes used as proxy indicators.
        """
        try:
            import requests  # type: ignore
        except ImportError:
            raise NotConfiguredError("'requests' package required. pip install requests")

        # Step 1: Get access token
        token_url = (
            f"https://api.videoindexer.ai/auth/{self._azure_location}"
            f"/Accounts/{self._azure_account}/AccessToken?allowEdit=false"
        )
        token_resp = requests.get(token_url, headers={"Ocp-Apim-Subscription-Key": self._azure_key}, timeout=30)
        token_resp.raise_for_status()
        access_token = token_resp.text.strip('"')

        # Step 2: Upload video
        upload_url = (
            f"https://api.videoindexer.ai/{self._azure_location}"
            f"/Accounts/{self._azure_account}/Videos?accessToken={access_token}"
            f"&name={ctx.file_name}&privacy=Private"
        )
        with open(ctx.file_path, "rb") as f:
            upload_resp = requests.post(upload_url, files={"file": f}, timeout=120)
        upload_resp.raise_for_status()
        video_id = upload_resp.json().get("id")

        # Step 3: Poll for completion (simplified — in production use Celery retry)
        import time
        for _ in range(30):
            time.sleep(10)
            status_url = (
                f"https://api.videoindexer.ai/{self._azure_location}"
                f"/Accounts/{self._azure_account}/Videos/{video_id}/Index"
                f"?accessToken={access_token}"
            )
            status_resp = requests.get(status_url, timeout=30)
            status_resp.raise_for_status()
            status_data = status_resp.json()
            if status_data.get("state") == "Processed":
                break

        # Heuristic: use face anomaly count as proxy for manipulation indicator
        insights = status_data.get("videos", [{}])[0].get("insights", {})
        anomaly_count = len(insights.get("emotions", []))
        ai_score: Optional[float] = None
        severity = "inconclusive"
        findings: List[Dict[str, Any]] = []

        findings.append({
            "indicator": "Video Manipulation Heuristic",
            "score": None,  # Azure VI does not return a single deepfake probability
            "explanation": (
                f"Azure Video Indexer processed the video. "
                f"{anomaly_count} emotion/face anomaly markers detected. "
                "No single deepfake probability is returned by this provider."
            ),
        })

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="Azure Video Indexer",
            model_version="2024-01",
            provider="Microsoft Azure",
            is_configured=True,
            score=None,   # Azure VI does not provide a single synthetic probability
            severity="inconclusive",  # Cannot derive severity without a calibrated score
            findings=findings,
            limitations=[
                "Azure Video Indexer does not return a calibrated AI-generation probability.",
                "Heuristic interpretation only — must not be used as proof of manipulation.",
                "Processing time increases significantly with video duration.",
            ],
            supports_frame_refs=False,
            supports_time_ranges=False,
        )


# ── AV Consistency adapter ────────────────────────────────────
class AVConsistencyAdapter(BaseDetectorAdapter):
    """
    Checks audio-video synchronisation consistency.
    Only run when:
      - Video has an audio track
      - AV_CONSISTENCY_CHECK=true
      - ffprobe is available (FFPROBE_PATH env or system PATH)

    Does NOT use an AI model — uses ffprobe stream metadata comparison.
    Returns offset_ms when detectable; does not fabricate offsets.
    """
    ADAPTER_KEY = "av_consistency_v1"
    MEDIA_TYPES = ["video"]

    supports_regions = False
    supports_frame_refs = False
    supports_time_ranges = False

    def __init__(self) -> None:
        self._enabled = os.getenv("AV_CONSISTENCY_CHECK", "false").lower() == "true"
        self._ffprobe = os.getenv("FFPROBE_PATH", "ffprobe")

    def is_configured(self) -> bool:
        if not self._enabled:
            return False
        import shutil
        return shutil.which(self._ffprobe) is not None

    def analyze(self, ctx: AdapterContext) -> DetectorResult:
        if not self.is_configured():
            raise NotConfiguredError(
                f"Adapter {self.ADAPTER_KEY} requires AV_CONSISTENCY_CHECK=true and ffprobe on PATH."
            )

        import json
        import subprocess

        cmd = [
            self._ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_streams", ctx.file_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return DetectorResult(
                adapter_key=self.ADAPTER_KEY,
                model_name="ffprobe AV Consistency",
                model_version="system",
                provider="FFmpeg/ffprobe",
                is_configured=True,
                score=None,
                severity="inconclusive",
                findings=[{"indicator": "ffprobe error", "explanation": proc.stderr[:500]}],
                limitations=["ffprobe failed to process the file."],
            )

        probe = json.loads(proc.stdout)
        streams = probe.get("streams", [])
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        video_streams = [s for s in streams if s.get("codec_type") == "video"]

        findings: List[Dict[str, Any]] = []
        offset_ms: Optional[float] = None
        severity = "inconclusive"

        if audio_streams and video_streams:
            v_start = float(video_streams[0].get("start_time", 0) or 0)
            a_start = float(audio_streams[0].get("start_time", 0) or 0)
            offset_ms = round(abs(v_start - a_start) * 1000, 2)
            severity = "high" if offset_ms > 200 else "medium" if offset_ms > 80 else "low"
            findings.append({
                "indicator": "AV Start Time Offset",
                "offset_ms": offset_ms,
                "explanation": (
                    f"Stream-level start-time difference: {offset_ms}ms. "
                    "Large offsets may indicate re-encoding or dubbing but are not proof of manipulation."
                ),
            })
        else:
            findings.append({
                "indicator": "Insufficient Streams",
                "explanation": "Could not compare streams — audio or video track missing.",
            })

        return DetectorResult(
            adapter_key=self.ADAPTER_KEY,
            model_name="ffprobe AV Consistency Check",
            model_version="system",
            provider="FFmpeg/ffprobe",
            is_configured=True,
            score=None,
            severity=severity,
            findings=findings,
            limitations=[
                "Stream start-time offset is metadata evidence, not proof of manipulation.",
                "Re-encoding, format conversion, or player differences can cause benign offsets.",
                "This check does not detect lip-sync desynchronisation within a stream.",
            ],
        )
