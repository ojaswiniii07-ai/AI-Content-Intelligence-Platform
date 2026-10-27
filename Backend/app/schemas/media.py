# ============================================================
#  Media Analysis — Pydantic schemas
#  Separate: AI indicators | similarity | quality | style
#  Never fabricate timestamps, regions, or percentages.
# ============================================================
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Enums ────────────────────────────────────────────────────
class MediaType(str, enum.Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"


# ── Shared primitives ─────────────────────────────────────────
class ModelInfo(BaseModel):
    """Always included in every finding so reviewers know what ran."""
    name: str
    version: str
    provider: str
    is_configured: bool
    limitations: List[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """
    A single piece of supporting evidence.
    All spatial/temporal fields are Optional — only populated when
    the detector actually supports localisation; never fabricated.
    """
    description: str
    # Image-only: bounding box in [x, y, w, h] normalised 0–1 when model supports it
    region: Optional[List[float]] = Field(
        default=None,
        description="Normalised [x,y,w,h] bounding box — present only when model supports spatial localisation",
    )
    # Video-only: frame index and second offset when model supports it
    frame_index: Optional[int] = Field(default=None, description="0-based frame index (video only, if supported)")
    timestamp_sec: Optional[float] = Field(default=None, description="Seconds from start (video only, if supported)")
    # Audio-only: time range in seconds when model supports it
    audio_start_sec: Optional[float] = Field(default=None, description="Audio segment start (audio/video only, if supported)")
    audio_end_sec: Optional[float] = Field(default=None, description="Audio segment end (audio/video only, if supported)")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Image ─────────────────────────────────────────────────────
class ImageFinding(BaseModel):
    """
    AI-involvement indicators for images.
    Separate from any similarity or quality dimension.
    """
    indicator: str
    severity: Severity
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0,
                                    description="Raw score from detector (0–1). None = unavailable.")
    evidence: List[Evidence] = Field(default_factory=list)
    explanation: str
    review_recommendation: str


# ── Audio ─────────────────────────────────────────────────────
class AudioFinding(BaseModel):
    indicator: str
    severity: Severity
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    # Time ranges only when adapter supports them
    time_ranges: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="[{start_sec, end_sec}] — present only when audio detector supports time localisation",
    )
    evidence: List[Evidence] = Field(default_factory=list)
    explanation: str
    review_recommendation: str


# ── Video ─────────────────────────────────────────────────────
class VideoFinding(BaseModel):
    indicator: str
    severity: Severity
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    # Frame / timestamp refs only when adapter supports them
    frame_references: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="[{frame_index, timestamp_sec, ...}] — only when detector supports frame-level output",
    )
    evidence: List[Evidence] = Field(default_factory=list)
    explanation: str
    review_recommendation: str


class AVConsistencyFinding(BaseModel):
    """Audio-video consistency — only populated when both tracks present and adapter configured."""
    indicator: str
    severity: Severity
    offset_ms: Optional[float] = None
    explanation: str
    review_recommendation: str


# ── Metadata (supporting evidence, not proof) ─────────────────
class MediaMetadata(BaseModel):
    """
    Extracted file metadata.
    Metadata is supporting context for human reviewers, NOT proof of manipulation.
    """
    file_name: str
    file_size_bytes: int
    content_type: str
    media_type: MediaType
    # Populated per media type
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    duration_sec: Optional[float] = None
    frame_count: Optional[int] = None
    fps: Optional[float] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    color_mode: Optional[str] = None
    has_audio_track: Optional[bool] = None
    has_video_track: Optional[bool] = None
    codec: Optional[str] = None
    exif: Dict[str, Any] = Field(default_factory=dict)
    caveat: str = (
        "File metadata is supporting context for human reviewers. "
        "Metadata alone is not proof of manipulation or synthetic origin."
    )


# ── Request / Response ────────────────────────────────────────
class MediaJobSubmitRequest(BaseModel):
    """Submitted after the file has already been uploaded (two-phase)."""
    upload_id: str = Field(description="ID returned by the /upload endpoint")
    detectors: List[str] = Field(
        default_factory=list,
        description=(
            "Explicit list of detector adapter keys to run. "
            "Leave empty to run all configured adapters for the media type."
        ),
    )
    workspace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MediaUploadResponse(BaseModel):
    upload_id: str
    file_name: str
    media_type: MediaType
    file_size_bytes: int
    storage_path: str          # Opaque internal path; NOT a public URL
    expires_at: datetime
    message: str = "File uploaded successfully. Call /submit with this upload_id to start analysis."


class MediaJobStatusResponse(BaseModel):
    job_id: str
    upload_id: str
    status: JobStatus
    media_type: Optional[MediaType] = None
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    error_message: Optional[str] = None


class MediaAnalysisResult(BaseModel):
    """
    Structured, multi-dimensional analysis result.
    AI-involvement, similarity, quality, and style are separate dimensions.
    Timestamp / frame / region fields are None when not supported by the
    configured adapter — they are never fabricated.
    """
    job_id: str
    upload_id: str
    media_type: MediaType
    file_metadata: MediaMetadata

    # ── Dimension 1: AI-involvement indicators ─────────────────
    ai_involvement_summary: Severity = Severity.INCONCLUSIVE
    ai_involvement_score: Optional[float] = Field(
        default=None,
        description="Aggregate AI-involvement score 0–1. None = inconclusive.",
    )
    image_findings: Optional[List[ImageFinding]] = None
    audio_findings: Optional[List[AudioFinding]] = None
    video_findings: Optional[List[VideoFinding]] = None
    av_consistency: Optional[AVConsistencyFinding] = None

    # ── Dimension 2: Writing quality (audio transcript quality if applicable) ──
    # Intentionally left minimal — expand if a quality adapter is configured
    quality_notes: Optional[str] = None

    # ── Dimension 3: Style alignment indicators ──────────────────
    style_notes: Optional[str] = None

    # ── Model provenance ─────────────────────────────────────────
    detectors_used: List[ModelInfo] = Field(default_factory=list)
    detectors_skipped: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Adapters that were requested but not configured, with reason.",
    )

    # ── Epistemic honesty ────────────────────────────────────────
    overall_verdict: str
    limitations: List[str] = Field(default_factory=list)
    caveat: str = (
        "These indicators are probabilistic decision-support signals, not proof of AI generation "
        "or manipulation. Metadata, timestamps, and region overlays are only reported when the "
        "configured detector explicitly supports them. Consequential decisions require human review."
    )
    review_recommended: bool = True
    analyzed_at: datetime
