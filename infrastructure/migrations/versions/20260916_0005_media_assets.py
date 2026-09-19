"""Add tenant-scoped image and video media assets.

Revision ID: 20260916_0005
Revises: 20260916_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260916_0005"
down_revision: str | None = "20260916_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("parent_asset_id", sa.Uuid(), nullable=True),
        sa.Column("media_type", sa.String(16), nullable=False),
        sa.Column("asset_role", sa.String(16), nullable=False),
        sa.Column("platform", sa.String(16), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("bytes_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("generation_provider", sa.String(120), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("asset_metadata", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "media_type IN ('image', 'video')",
            name=op.f("ck_media_assets_valid_media_asset_type"),
        ),
        sa.CheckConstraint(
            "asset_role IN ('source', 'generated', 'variant', 'composition')",
            name=op.f("ck_media_assets_valid_media_asset_role"),
        ),
        sa.CheckConstraint(
            "status IN ('processing', 'ready', 'failed')",
            name=op.f("ck_media_assets_valid_media_asset_status"),
        ),
        sa.CheckConstraint(
            "platform IS NULL OR platform IN ('linkedin', 'instagram', 'threads', 'x', 'facebook', 'youtube')",
            name=op.f("ck_media_assets_valid_media_asset_platform"),
        ),
        sa.CheckConstraint(
            "bytes_size >= 0", name=op.f("ck_media_assets_valid_media_asset_bytes")
        ),
        sa.CheckConstraint(
            "width IS NULL OR width > 0",
            name=op.f("ck_media_assets_valid_media_asset_width"),
        ),
        sa.CheckConstraint(
            "height IS NULL OR height > 0",
            name=op.f("ck_media_assets_valid_media_asset_height"),
        ),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name=op.f("ck_media_assets_valid_media_asset_duration"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id", "workspace_id"],
            ["campaigns.id", "campaigns.workspace_id"],
            name=op.f("fk_media_assets_campaign_id_campaigns"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_media_assets_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_media_assets_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_asset_id"],
            ["media_assets.id"],
            name=op.f("fk_media_assets_parent_asset_id_media_assets"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_assets")),
        sa.UniqueConstraint("id", "workspace_id", name="uq_media_assets_id_workspace"),
        sa.UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
    )
    for column in (
        "workspace_id",
        "campaign_id",
        "created_by_user_id",
        "parent_asset_id",
    ):
        op.create_index(op.f(f"ix_media_assets_{column}"), "media_assets", [column])
    op.create_index(
        "ix_media_assets_workspace_created",
        "media_assets",
        ["workspace_id", "created_at"],
    )
    op.create_index(
        "ix_media_assets_workspace_campaign",
        "media_assets",
        ["workspace_id", "campaign_id"],
    )


def downgrade() -> None:
    op.drop_table("media_assets")
