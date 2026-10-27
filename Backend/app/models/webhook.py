"""
WebhookEndpoint and WebhookDelivery models.

Security design
---------------
* Each endpoint stores a Fernet-encrypted HMAC-SHA256 signing secret.
  The secret is generated server-side at creation time and shown ONCE to the
  caller in the creation response.  It is never returned again.
* Every outgoing event is signed:
    X-ContentIQ-Signature-256: sha256=<HMAC-SHA256(secret, body)>
    X-ContentIQ-Event-ID: <uuid>
    X-ContentIQ-Timestamp: <unix_seconds>
  Callers verify the signature to reject tampered payloads.
* Replay protection: deliveries include timestamp; callers should reject events
  whose timestamp differs from the current time by more than REPLAY_WINDOW_SECS.

Delivery lifecycle
------------------
  pending → attempted → delivered | failed | exhausted

Retry policy
------------
  MAX_ATTEMPTS = 5  (exponential back-off: 30s, 2m, 8m, 32m, 2h)
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.integration import Integration


class WebhookEndpoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A registered outgoing webhook endpoint belonging to an integration.

    An integration may have multiple endpoints (e.g. one for job completion,
    one for failure alerts).
    """
    __tablename__ = "webhook_endpoints"

    integration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("integrations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    # Destination URL supplied by the caller
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Human-readable label
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Which event types trigger this endpoint
    # e.g. ["job.completed", "job.failed", "batch.done", "batch.partial_failure"]
    event_types: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    # Fernet-encrypted HMAC signing secret.
    # Generated server-side; shown once to caller in creation response; never returned again.
    encrypted_signing_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Whether the endpoint is active (paused/enabled by the user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Include full result payload in delivery? (Only when explicitly configured)
    include_full_payload: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Connection status from last test
    last_test_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_test_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Delivery counts
    total_delivered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="webhook_endpoints"
    )
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan"
    )


class WebhookDelivery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Immutable log entry for a single outgoing webhook delivery attempt.

    One delivery record is created per attempt.  On retry, a new record is
    created linking to the same endpoint and event_id.
    """
    __tablename__ = "webhook_deliveries"

    endpoint_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    # Unique, idempotent event identifier — same across all retry attempts
    event_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    # Event type: "job.completed" | "job.failed" | "batch.done" | etc.
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Attempt number (1-based)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Status: pending | attempted | delivered | failed | exhausted
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)

    # HTTP response from the target
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body_truncated: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Delivery metadata
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # The event timestamp embedded in the signature header (Unix seconds)
    event_timestamp: Mapped[int] = mapped_column(Integer, nullable=False)

    # SHA256 signature that was sent
    signature_header: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Error message (if delivery failed)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Reference IDs (submission or batch that triggered this event)
    submission_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)

    # Relationships
    endpoint: Mapped["WebhookEndpoint"] = relationship(
        "WebhookEndpoint", back_populates="deliveries"
    )
