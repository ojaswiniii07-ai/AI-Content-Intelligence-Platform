from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.submission import Submission


class AnalysisJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_jobs"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # text_analysis, media_deepfake, similarity
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True, nullable=False)  # queued, processing, completed, failed
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="jobs")
    results: Mapped[List["AnalysisResult"]] = relationship("AnalysisResult", back_populates="job", cascade="all, delete-orphan")


class AnalysisResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_results"

    job_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("analysis_jobs.id", ondelete="SET NULL"), index=True, nullable=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False)
    
    model_version: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # text-detector-v2.4
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0 to 100 percentage
    ai_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    confidence_level: Mapped[str] = mapped_column(String(50), nullable=False)  # High, Medium, Low, Inconclusive
    verdict: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Likely AI, Inconclusive, Likely Human

    # Detailed signals and visualizations
    # dimensions: {"AI-Typical Phrasing": 74, "Structural Patterns": 61, "Source Similarity": 22, "Style Consistency": 88}
    dimensions: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    # sentence_spans: [{"text": "...", "heat": "high", "start": 0, "end": 64}]
    sentence_spans: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    # media_anomalies: [{"frame": 4, "time": "0:04", "type": "Face Blend", "severity": "orange", "desc": "..."}]
    media_anomalies: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    # raw_metadata: key-value dictionary of raw detector diagnostics
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="results")
    job: Mapped[Optional["AnalysisJob"]] = relationship("AnalysisJob", back_populates="results")
