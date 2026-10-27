"""Add batch orchestration fields.

Revision ID: 005
Revises: 004
Create Date: 2026-10-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new orchestration columns to batches
    with op.batch_alter_table("batches") as batch_op:
        batch_op.add_column(
            sa.Column(
                "analysis_types",
                sa.JSON().with_variant(postgresql.JSONB, "postgresql"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "rubric_id",
                sa.String(length=36),
                sa.ForeignKey("rubrics.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "failed_items",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "failure_details",
                sa.JSON().with_variant(postgresql.JSONB, "postgresql"),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("batches") as batch_op:
        batch_op.drop_column("failure_details")
        batch_op.drop_column("failed_items")
        batch_op.drop_column("rubric_id")
        batch_op.drop_column("analysis_types")
