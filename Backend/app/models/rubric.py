from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.review import Review
    from app.models.user import User


class Rubric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rubrics"

    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Versioning & Lifecycle
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True, nullable=False)  # draft, published, archived
    parent_rubric_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True)
    created_by_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # weights: {"relevance": 0.35, "reasoning": 0.35, "originality": 0.30}
    weights: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    # criteria: list of criterion definitions, descriptions, required points, weights
    criteria: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    # scoring_scale: min_score, max_score, step, levels
    scoring_scale: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    # style_rules: optional style constraints (e.g. word count, tone, format)
    style_rules: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="rubrics")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="rubric")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    parent_rubric: Mapped[Optional["Rubric"]] = relationship("Rubric", remote_side="Rubric.id", foreign_keys=[parent_rubric_id])
