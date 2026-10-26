from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.review import Review


class Rubric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rubrics"

    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # weights: {"relevance": 0.35, "reasoning": 0.35, "originality": 0.30}
    weights: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    # criteria: list of criterion definitions, descriptions, and point scales
    criteria: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="rubrics")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="rubric")
