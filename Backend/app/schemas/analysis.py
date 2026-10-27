from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# --- Text Analysis Schemas ---
class SentenceSpan(BaseModel):
    text: str
    heat: str  # low, mid, high
    start: Optional[int] = None
    end: Optional[int] = None


class DimensionScore(BaseModel):
    name: str
    pct: float
    description: Optional[str] = None


class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000)
    cross_reference_similarity: bool = True
    prompt_hypothesis: bool = False
    style_alignment: bool = False
    workspace_id: Optional[str] = None
    title: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    id: str
    overall_score: float  # 0 to 100
    ai_probability: float  # 0.0 to 1.0
    confidence_level: str  # High, Medium, Low, Inconclusive
    verdict: str  # Likely AI, Inconclusive, Likely Human
    word_count: int
    char_count: int
    model_version: str
    sentence_spans: List[SentenceSpan]
    dimensions: List[DimensionScore]
    caveat: str
    analyzed_at: datetime


class TextSpan(BaseModel):
    text: str
    label: str  # 'AI' | 'Human'
    score: float
    heat: str  # low, mid, high
    start: int
    end: int


class SpanDocumentSummary(BaseModel):
    total_sentences: int = 0
    ai_sentences: int = 0
    human_sentences: int = 0
    ai_percentage: float = 0.0
    ai_char_pct: float = 0.0
    avg_ai_score: float = 0.0
    avg_human_score: float = 0.0


class SpanDetectionResponse(BaseModel):
    document_summary: SpanDocumentSummary
    sentence_spans: List[TextSpan]
    merged_blocks: List[TextSpan]
    model_version: str
    threshold: float


# --- Media Analysis Schemas ---
class MediaAnomaly(BaseModel):
    frame: int
    timestamp_str: str
    type: str
    severity: str  # green, yellow, orange, red
    description: str


class MediaAnalysisRequest(BaseModel):
    file_name: Optional[str] = "media_sample.mp4"
    file_url: Optional[str] = None
    content_type: Optional[str] = None
    media_type: Optional[str] = None
    detectors: List[str] = [
        "Face Blend Artifacts",
        "Lighting Inconsistency",
        "Facial Motion",
        "Audio/Video Sync",
    ]
    workspace_id: Optional[str] = None

    @model_validator(mode="after")
    def resolve_content_type(self) -> "MediaAnalysisRequest":
        ct = self.content_type or self.media_type or "video"
        if ct not in ("image", "video", "audio"):
            ct = "video"
        self.content_type = ct
        return self


class MediaAnalysisResponse(BaseModel):
    id: str
    synthetic_probability: float  # percentage 0 to 100
    confidence_level: str
    verdict: str
    model_version: str
    active_detectors: List[str]
    anomalies: List[MediaAnomaly]
    caveat: str
    analyzed_at: datetime


# --- FP/FN Simulator Schemas ---
class SimulatorRequest(BaseModel):
    model_version: str = "text-detector-v2.4"
    dataset: str = "edu-2400"
    threshold: float = Field(default=0.60, ge=0.0, le=1.0)


class ConfusionMatrix(BaseModel):
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    total_samples: int


class SimulatorResponse(BaseModel):
    threshold: float
    model_version: str
    dataset: str
    false_positive_rate: float
    false_negative_rate: float
    precision: float
    recall: float
    confusion_matrix: ConfusionMatrix
    recommendation: str
    caveat: str


# --- Video Deepfake Detection Schemas ---

class FrameAnalysisResult(BaseModel):
    """Per-frame result from the local deepfake model."""
    frame_index: int
    fake_probability: float
    verdict: str           # Fake | Real | No Face
    confidence: str        # High | Medium | Low
    face_detected: bool


class VideoDeepfakeRequest(BaseModel):
    """
    Request body for /analysis/video-deepfake.
    Accepts an upload_id (returned by POST /media/upload) or a raw file path
    for testing.
    """
    upload_id: Optional[str] = None
    file_path: Optional[str] = None   # Absolute server-side path (for integration tests)
    n_frames: int = Field(default=16, ge=1, le=64, description="Number of frames to sample")

    @model_validator(mode="after")
    def require_one_source(self) -> "VideoDeepfakeRequest":
        if not self.upload_id and not self.file_path:
            raise ValueError("Provide either upload_id or file_path")
        return self


class VideoDeepfakeResponse(BaseModel):
    """Full response from the local EfficientNet-B0 + MTCNN video deepfake detector."""
    id: str
    fake_probability: float           # 0.0 – 1.0
    overall_score: float              # 0.0 – 100.0
    verdict: str                      # e.g. "Likely Deepfake"
    confidence_level: str             # e.g. "High Confidence"
    model_version: str
    total_frames_sampled: int
    faces_detected: int
    frame_results: List[FrameAnalysisResult]
    aggregation_method: str
    adapter: str                      # "local_video_deepfake_v1"
    caveat: str
    analyzed_at: datetime

