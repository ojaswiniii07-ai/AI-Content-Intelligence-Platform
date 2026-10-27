from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User


class AuditEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_events"

    workspace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="SET NULL"), index=True, nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    # Event categories: Submission Analyzed, Reviewer Decision, Override Recorded, Model Updated, Batch Export, Security Tamper Alert
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # submission, batch, model, system, review
    target_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    decision_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Uncertainty status: supported, inconclusive, not_configured, failed
    uncertainty_status: Mapped[str] = mapped_column(String(50), default="supported", index=True, nullable=False)
    rubric_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1", nullable=True)

    # Permitted evidence references (offsets, timestamps, hashes — sanitized without full text)
    evidence_references: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Cryptographic verification & tamper detection
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    prev_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tamper_status: Mapped[str] = mapped_column(String(50), default="Verified", nullable=False)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace", back_populates="audit_events")
    actor: Mapped[Optional["User"]] = relationship("User", back_populates="audit_events")
