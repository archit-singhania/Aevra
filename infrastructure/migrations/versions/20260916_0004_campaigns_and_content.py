"""Create tenant-scoped campaign orchestration and content tables.

Revision ID: 20260916_0004
Revises: 20260915_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_0004"
down_revision: str | None = "20260915_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("product_service", sa.String(300), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("platforms", sa.JSON(), nullable=False),
        sa.Column("media_types", sa.JSON(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publishing_mode", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_revision", sa.Integer(), nullable=False),
        sa.Column("latest_feedback", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "publishing_mode IN ('manual', 'assisted', 'autonomous')",
            name=op.f("ck_campaigns_valid_campaign_publishing_mode"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'context_retrieval', 'planning', 'content_generation', "
            "'platform_adaptation', 'validation', 'awaiting_approval', 'approved', "
            "'failed', 'cancelled')",
            name=op.f("ck_campaigns_valid_campaign_status"),
        ),
        sa.CheckConstraint(
            "current_revision >= 0", name=op.f("ck_campaigns_valid_campaign_revision")
        ),
        sa.ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brand_profiles.id", "brand_profiles.workspace_id"],
            name=op.f("fk_campaigns_brand_id_brand_profiles"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_campaigns_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_campaigns_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaigns")),
        sa.UniqueConstraint("id", "workspace_id", name="uq_campaigns_id_workspace"),
    )
    for column in ("workspace_id", "brand_id", "created_by_user_id"):
        op.create_index(op.f(f"ix_campaigns_{column}"), "campaigns", [column])
    op.create_index(
        "ix_campaigns_workspace_created", "campaigns", ["workspace_id", "created_at"]
    )

    op.create_table(
        "campaign_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("current_node", sa.String(64), nullable=True),
        sa.Column("state_snapshot", sa.JSON(), nullable=False),
        sa.Column("provider_metadata", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "run_number > 0", name=op.f("ck_campaign_runs_valid_run_number")
        ),
        sa.CheckConstraint(
            "status IN ('running', 'waiting_approval', 'completed', 'failed', 'cancelled')",
            name=op.f("ck_campaign_runs_valid_status"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id", "workspace_id"],
            ["campaigns.id", "campaigns.workspace_id"],
            name=op.f("fk_campaign_runs_campaign_id_campaigns"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_runs")),
        sa.UniqueConstraint("id", "campaign_id", "workspace_id", name="uq_runs_scope"),
        sa.UniqueConstraint("campaign_id", "run_number", name="uq_campaign_run_number"),
    )
    op.create_index(
        op.f("ix_campaign_runs_workspace_id"), "campaign_runs", ["workspace_id"]
    )
    op.create_index(
        op.f("ix_campaign_runs_campaign_id"), "campaign_runs", ["campaign_id"]
    )
    op.create_index(
        "ix_campaign_runs_workspace_campaign",
        "campaign_runs",
        ["workspace_id", "campaign_id"],
    )

    op.create_table(
        "campaign_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("node_name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("output_snapshot", sa.JSON(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("provider_metadata", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "sequence > 0", name=op.f("ck_campaign_steps_valid_sequence")
        ),
        sa.CheckConstraint(
            "status IN ('completed', 'failed')",
            name=op.f("ck_campaign_steps_valid_status"),
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "campaign_id", "workspace_id"],
            [
                "campaign_runs.id",
                "campaign_runs.campaign_id",
                "campaign_runs.workspace_id",
            ],
            name=op.f("fk_campaign_steps_run_id_campaign_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_steps")),
        sa.UniqueConstraint("run_id", "sequence", name="uq_campaign_step_sequence"),
    )
    for column in ("workspace_id", "campaign_id", "run_id"):
        op.create_index(op.f(f"ix_campaign_steps_{column}"), "campaign_steps", [column])
    op.create_index(
        "ix_campaign_steps_workspace_run", "campaign_steps", ["workspace_id", "run_id"]
    )

    op.create_table(
        "content_variants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("title", sa.String(300), nullable=True),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.JSON(), nullable=False),
        sa.Column("call_to_action", sa.String(500), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("validation_issues", sa.JSON(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("generated_by_model", sa.String(160), nullable=False),
        sa.Column("generation_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "revision > 0", name=op.f("ck_content_variants_valid_revision")
        ),
        sa.CheckConstraint(
            "platform IN ('linkedin', 'instagram', 'threads', 'x', 'facebook', 'youtube')",
            name=op.f("ck_content_variants_valid_platform"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'rejected', 'superseded')",
            name=op.f("ck_content_variants_valid_status"),
        ),
        sa.CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100",
            name=op.f("ck_content_variants_valid_quality_score"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id", "workspace_id"],
            ["campaigns.id", "campaigns.workspace_id"],
            name=op.f("fk_content_variants_campaign_id_campaigns"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_variants")),
        sa.UniqueConstraint(
            "campaign_id",
            "revision",
            "platform",
            name="uq_variant_campaign_revision_platform",
        ),
    )
    op.create_index(
        op.f("ix_content_variants_workspace_id"), "content_variants", ["workspace_id"]
    )
    op.create_index(
        op.f("ix_content_variants_campaign_id"), "content_variants", ["campaign_id"]
    )
    op.create_index(
        "ix_content_variants_workspace_campaign",
        "content_variants",
        ["workspace_id", "campaign_id"],
    )


def downgrade() -> None:
    op.drop_table("content_variants")
    op.drop_table("campaign_steps")
    op.drop_table("campaign_runs")
    op.drop_table("campaigns")
