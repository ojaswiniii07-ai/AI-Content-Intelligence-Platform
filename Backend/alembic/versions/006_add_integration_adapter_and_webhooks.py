"""Add integration adapter and webhook tables.

Revision ID: 006
Revises: 005
Create Date: 2026-10-27

Changes
-------
1. Extend integrations table with new columns:
   - display_name, auth_method, encrypted_secrets, oauth_data
   - connection_status, connection_error, last_connection_test_at
   - total_submissions_received

2. Create webhook_endpoints table.

3. Create webhook_deliveries table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Extend integrations ──────────────────────────────────────────────
    with op.batch_alter_table("integrations") as t:
        t.add_column(sa.Column("display_name", sa.String(255), nullable=False, server_default="Integration"))
        t.add_column(sa.Column("auth_method", sa.String(50), nullable=False, server_default="api_key"))
        t.add_column(sa.Column("encrypted_secrets", sa.Text, nullable=True))
        t.add_column(
            sa.Column(
                "oauth_data",
                sa.JSON().with_variant(postgresql.JSONB, "postgresql"),
                nullable=True,
            )
        )
        t.add_column(sa.Column("connection_status", sa.String(50), nullable=False, server_default="not_configured"))
        t.add_column(sa.Column("connection_error", sa.String(500), nullable=True))
        t.add_column(sa.Column("last_connection_test_at", sa.DateTime(timezone=True), nullable=True))
        t.add_column(sa.Column("total_submissions_received", sa.Integer, nullable=False, server_default="0"))

    # ── 2. webhook_endpoints ────────────────────────────────────────────────
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("integration_id", sa.String(36), sa.ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("event_types", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True),
        sa.Column("encrypted_signing_secret", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("include_full_payload", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("last_test_status", sa.String(50), nullable=True),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_delivered", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── 3. webhook_deliveries ───────────────────────────────────────────────
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("endpoint_id", sa.String(36), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_id", sa.String(36), nullable=False, index=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("http_status_code", sa.Integer, nullable=True),
        sa.Column("response_body_truncated", sa.String(500), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_timestamp", sa.Integer, nullable=False),
        sa.Column("signature_header", sa.String(100), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("submission_id", sa.String(36), nullable=True, index=True),
        sa.Column("batch_id", sa.String(36), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
    with op.batch_alter_table("integrations") as t:
        t.drop_column("total_submissions_received")
        t.drop_column("last_connection_test_at")
        t.drop_column("connection_error")
        t.drop_column("connection_status")
        t.drop_column("oauth_data")
        t.drop_column("encrypted_secrets")
        t.drop_column("auth_method")
        t.drop_column("display_name")
