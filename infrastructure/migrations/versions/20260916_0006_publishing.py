"""Add social accounts and idempotent publish jobs.

Revision ID: 20260916_0006
Revises: 20260916_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_0006"
down_revision: str | None = "20260916_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("external_account_id", sa.String(300), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("access_token_ref", sa.String(512), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("account_metadata", sa.JSON(), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "platform IN ('linkedin', 'instagram', 'threads', 'x', 'facebook', 'youtube')",
            name=op.f("ck_social_accounts_valid_social_account_platform"),
        ),
        sa.CheckConstraint(
            "status IN ('connected', 'paused', 'revoked')",
            name=op.f("ck_social_accounts_valid_social_account_status"),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "platform",
            "external_account_id",
            name="uq_social_account_identity",
        ),
    )
    op.create_index(
        "ix_social_accounts_workspace_id", "social_accounts", ["workspace_id"]
    )
    op.create_index(
        "ix_social_accounts_created_by_user_id",
        "social_accounts",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_social_accounts_workspace_platform",
        "social_accounts",
        ["workspace_id", "platform"],
    )

    op.create_table(
        "publish_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("social_account_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("external_post_id", sa.String(300), nullable=True),
        sa.Column("external_url", sa.String(2048), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('queued', 'publishing', 'published', 'verified', 'failed', 'cancelled')",
            name=op.f("ck_publish_jobs_valid_publish_job_status"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id", "workspace_id"],
            ["campaigns.id", "campaigns.workspace_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["social_account_id"], ["social_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id", "idempotency_key", name="uq_publish_job_idempotency"
        ),
    )
    for column in (
        "workspace_id",
        "campaign_id",
        "social_account_id",
        "created_by_user_id",
    ):
        op.create_index(op.f(f"ix_publish_jobs_{column}"), "publish_jobs", [column])
    op.create_index(
        "ix_publish_jobs_workspace_created",
        "publish_jobs",
        ["workspace_id", "created_at"],
    )
    op.create_index(
        "ix_publish_jobs_workspace_campaign",
        "publish_jobs",
        ["workspace_id", "campaign_id"],
    )


def downgrade() -> None:
    op.drop_table("publish_jobs")
    op.drop_table("social_accounts")
