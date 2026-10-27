"""
SQLAlchemy model for media analysis jobs.
Tracks: upload → submit → worker execution → result storage.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class MediaJobStatusEnum(str):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class MediaJob(Base):
    __tablename__ = "media_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(String(64), nullable=False, index=True, unique=True)

    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(String(64), nullable=True)

    # File info (no plaintext path exposed to API consumers)
    original_file_name = Column(String(512), nullable=False)
    file_size_bytes = Column(String(32), nullable=False)  # store as string to avoid bigint driver quirks
    content_type = Column(String(128), nullable=False)
    media_type = Column(String(16), nullable=False)   # image | audio | video
    storage_path = Column(String(1024), nullable=False)  # opaque internal path

    # Processing
    status = Column(String(32), nullable=False, default="pending")
    celery_task_id = Column(String(256), nullable=True)
    worker_id = Column(String(256), nullable=True)
    requested_detectors = Column(JSON, nullable=True)

    # Timings
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # temp file expiry

    # Result + error
    result_payload = Column(JSON, nullable=True)   # full MediaAnalysisResult dict
    error_message = Column(String(2048), nullable=True)
    request_metadata = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_media_jobs_user_id", "user_id"),
        Index("ix_media_jobs_status", "status"),
        Index("ix_media_jobs_submitted_at", "submitted_at"),
    )
