"""
003_add_rubric_evaluation_fields.py — adds versioning, lifecycle status, criteria and detailed evaluation fields to rubrics and reviews.

Run:
  alembic upgrade head
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_add_rubric_evaluation_fields"
down_revision = "002_add_media_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Rubrics columns ────────────────────────────────────────────────────────
    op.add_column("rubrics", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("rubrics", sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"))
    op.add_column("rubrics", sa.Column("parent_rubric_id", sa.String(length=36), sa.ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True))
    op.add_column("rubrics", sa.Column("created_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("rubrics", sa.Column("scoring_scale", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.add_column("rubrics", sa.Column("style_rules", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.create_index("ix_rubrics_status", "rubrics", ["status"], unique=False)

    # ── Reviews columns ────────────────────────────────────────────────────────
    op.add_column("reviews", sa.Column("criterion_scores", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.add_column("reviews", sa.Column("missing_requirements", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.add_column("reviews", sa.Column("evaluation_metadata", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True))
    op.add_column("reviews", sa.Column("ai_signal", sa.String(length=50), nullable=True, server_default="Unanalyzed"))
    op.add_column("reviews", sa.Column("ai_score", sa.Float(), nullable=True, server_default="0.0"))
    op.add_column("reviews", sa.Column("similarity_score", sa.Float(), nullable=True, server_default="0.0"))
    op.add_column("reviews", sa.Column("rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    # Reviews
    op.drop_column("reviews", "rank")
    op.drop_column("reviews", "similarity_score")
    op.drop_column("reviews", "ai_score")
    op.drop_column("reviews", "ai_signal")
    op.drop_column("reviews", "evaluation_metadata")
    op.drop_column("reviews", "missing_requirements")
    op.drop_column("reviews", "criterion_scores")

    # Rubrics
    op.drop_index("ix_rubrics_status", table_name="rubrics")
    op.drop_column("rubrics", "style_rules")
    op.drop_column("rubrics", "scoring_scale")
    op.drop_column("rubrics", "created_by_id")
    op.drop_column("rubrics", "parent_rubric_id")
    op.drop_column("rubrics", "status")
    op.drop_column("rubrics", "version")
