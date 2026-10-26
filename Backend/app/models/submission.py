from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User
    from app.models.batch import Batch
    from app.models.analysis import AnalysisJob, AnalysisResult
    from app.models.review import Review


class Submission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submissions"

    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    submitter_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("batches.id", ondelete="SET NULL"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)  # text, image, video, audio
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status: pending, analyzing, completed, flagged, shortlisted, rejected
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    source_identifier: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)  # e.g. sub_0041

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="submissions")
    submitter: Mapped[Optional["User"]] = relationship("User", back_populates="submissions")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="submissions")
    
    jobs: Mapped[List["AnalysisJob"]] = relationship("AnalysisJob", back_populates="submission", cascade="all, delete-orphan")
    results: Mapped[List["AnalysisResult"]] = relationship("AnalysisResult", back_populates="submission", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="submission", cascade="all, delete-orphan")
