"""
Integration model — stores adapter configuration for external platforms.

Security rules
--------------
* Secrets (API keys, OAuth tokens) are stored ONLY as Fernet-encrypted bytes
  in the  encrypted_secrets  column.  The  config  column holds non-sensitive
  metadata (base URLs, form IDs, LMS course IDs, etc.) in plain JSON.
* The  encrypted_secrets  field is never returned by any API endpoint.
* OAuth refresh tokens are encrypted and stored separately in  oauth_data.
* connection_status reflects the last verified connection check result.

Provider constants
------------------
  google_forms  — Google Forms API v1 (OAuth2, read-only Forms scope)
  typeform      — Typeform Responses API (Personal Access Token or OAuth2)
  canvas_lms    — Canvas LMS REST API (Bearer token, explicit scopes)
  moodle        — Moodle Web Services API (Token, wsfunction-based)
  blackboard    — Blackboard REST API (OAuth2 client credentials)
  custom        — Generic HTTP webhook / API client
  mock          — In-memory mock adapter for tests
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.webhook import WebhookEndpoint


class Integration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores a single external platform connection for a workspace."""
    __tablename__ = "integrations"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    # Provider key — must match an adapter registry entry
    provider: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Human-readable label (e.g. "Hackathon 2026 Forms")
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Non-sensitive configuration: base_url, form_id, course_id, scopes list, etc.
    config: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    # Fernet-encrypted blob storing API keys / OAuth tokens.
    # Contents: JSON bytes — {"api_key": "...", "access_token": "..."}
    # NEVER returned to clients.
    encrypted_secrets: Mapped[Optional[bytes]] = mapped_column(
        Text, nullable=True
    )

    # OAuth-specific metadata (non-secret): token_type, scope, expires_at, etc.
    oauth_data: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    # Auth method: api_key | oauth2 | client_credentials | pat | none
    auth_method: Mapped[str] = mapped_column(
        String(50), default="api_key", nullable=False
    )

    # Status: connected | disconnected | error | pending | not_configured
    connection_status: Mapped[str] = mapped_column(
        String(50), default="not_configured", index=True, nullable=False
    )
    connection_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_connection_test_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # How many submissions this integration has delivered
    total_submissions_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="integrations")
    webhook_endpoints: Mapped[list["WebhookEndpoint"]] = relationship(
        "WebhookEndpoint", back_populates="integration", cascade="all, delete-orphan"
    )
