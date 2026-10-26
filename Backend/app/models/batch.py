from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.submission import Submission


class Batch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "batches"

    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), default="Direct Upload", nullable=False)  # CSV Upload, API, LMS Sync
    file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flagged_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Status: queued, running, done, failed
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True, nullable=False)

    # score_distribution: {"0-20%": 42, "20-40%": 26, "40-60%": 12, "60-80%": 13, "80-100%": 7}
    score_distribution: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="batches")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="batch")
