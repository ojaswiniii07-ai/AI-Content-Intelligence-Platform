"""
004_add_audit_uncertainty_and_lineage.py — adds uncertainty status, rubric/result versions, evidence references, and metadata to audit_events.

Run:
  alembic upgrade head
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_add_audit_uncertainty_and_lineage"
down_revision = "003_add_rubric_evaluation_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_events", sa.Column("uncertainty_status", sa.String(length=50), nullable=False, server_default="supported"))
    op.add_column("audit_events", sa.Column("rubric_version", sa.Integer(), nullable=True))
    op.add_column("audit_events", sa.Column("result_version", sa.String(length=50), nullable=True, server_default="v1"))
    op.add_column("audit_events", sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.add_column("audit_events", sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.create_index("ix_audit_events_uncertainty_status", "audit_events", ["uncertainty_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_uncertainty_status", table_name="audit_events")
    op.drop_column("audit_events", "raw_metadata")
    op.drop_column("audit_events", "evidence_references")
    op.drop_column("audit_events", "result_version")
    op.drop_column("audit_events", "rubric_version")
    op.drop_column("audit_events", "uncertainty_status")
