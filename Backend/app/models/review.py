from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.user import User
    from app.models.rubric import Rubric


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reviews"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    rubric_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("rubrics.id", ondelete="SET NULL"), index=True, nullable=True)

    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0 to 10
    reasoning_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0 to 10
    originality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0 to 10
    total_score: Mapped[float] = mapped_column(Float, default=0.0, index=True, nullable=False)  # percentage 0 to 100

    # Decision status: shortlisted, pending, flagged, rejected
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)

    # Detailed evaluation results
    criterion_scores: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    missing_requirements: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    evaluation_metadata: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Decoupled signals (strictly informational — do NOT affect quality score)
    ai_signal: Mapped[Optional[str]] = mapped_column(String(50), default="Unanalyzed", nullable=True)  # Low, Medium, High
    ai_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # PRD Compliance: Explicit human override and rationale
    override_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User", back_populates="reviews")
    rubric: Mapped[Optional["Rubric"]] = relationship("Rubric", back_populates="reviews")
