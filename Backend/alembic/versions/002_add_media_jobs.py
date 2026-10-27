"""
002_add_media_jobs.py — adds the media_jobs table.

Run:
  alembic upgrade head
  # or explicitly:
  alembic upgrade 002_add_media_jobs
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_add_media_jobs"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_id", sa.String(64), nullable=False, unique=True),
        # Ownership
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.String(64), nullable=True),
        # File info
        sa.Column("original_file_name", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.String(32), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("media_type", sa.String(16), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        # Processing
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("celery_task_id", sa.String(256), nullable=True),
        sa.Column("worker_id", sa.String(256), nullable=True),
        sa.Column("requested_detectors", sa.JSON, nullable=True),
        # Timings
        sa.Column("submitted_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        # Result + error
        sa.Column("result_payload", sa.JSON, nullable=True),
        sa.Column("error_message", sa.String(2048), nullable=True),
        sa.Column("request_metadata", sa.JSON, nullable=True),
    )

    op.create_index("ix_media_jobs_upload_id", "media_jobs", ["upload_id"])
    op.create_index("ix_media_jobs_user_id", "media_jobs", ["user_id"])
    op.create_index("ix_media_jobs_status", "media_jobs", ["status"])
    op.create_index("ix_media_jobs_submitted_at", "media_jobs", ["submitted_at"])


def downgrade() -> None:
    op.drop_index("ix_media_jobs_submitted_at", table_name="media_jobs")
    op.drop_index("ix_media_jobs_status", table_name="media_jobs")
    op.drop_index("ix_media_jobs_user_id", table_name="media_jobs")
    op.drop_index("ix_media_jobs_upload_id", table_name="media_jobs")
    op.drop_table("media_jobs")
