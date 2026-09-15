"""Create tenant-scoped brand profiles and rules.

Revision ID: 20260915_0002
Revises: 20260915_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260915_0002"
down_revision: str | None = "20260915_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("tone_attributes", sa.JSON(), nullable=False),
        sa.Column("target_audiences", sa.JSON(), nullable=False),
        sa.Column("preferred_ctas", sa.JSON(), nullable=False),
        sa.Column("preferred_hashtags", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name=op.f("ck_brand_profiles_valid_brand_status"),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_brand_profiles_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_profiles")),
        sa.UniqueConstraint(
            "id", "workspace_id", name="uq_brand_profiles_id_workspace"
        ),
        sa.UniqueConstraint(
            "workspace_id", "slug", name=op.f("uq_brand_profiles_workspace_id")
        ),
    )
    op.create_index(
        op.f("ix_brand_profiles_workspace_id"),
        "brand_profiles",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_brand_profiles_workspace_created",
        "brand_profiles",
        ["workspace_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "brand_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("enforcement", sa.String(length=16), nullable=False),
        sa.Column("directive", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('voice', 'claim', 'cta', 'terminology', 'compliance')",
            name=op.f("ck_brand_rules_valid_brand_rule_category"),
        ),
        sa.CheckConstraint(
            "enforcement IN ('required', 'preferred', 'prohibited')",
            name=op.f("ck_brand_rules_valid_brand_rule_enforcement"),
        ),
        sa.CheckConstraint(
            "priority BETWEEN 1 AND 100",
            name=op.f("ck_brand_rules_valid_brand_rule_priority"),
        ),
        sa.ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brand_profiles.id", "brand_profiles.workspace_id"],
            name=op.f("fk_brand_rules_brand_id_brand_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_brand_rules_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_rules")),
    )
    op.create_index(
        op.f("ix_brand_rules_brand_id"), "brand_rules", ["brand_id"], unique=False
    )
    op.create_index(
        op.f("ix_brand_rules_created_by_user_id"),
        "brand_rules",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_brand_rules_workspace_id"),
        "brand_rules",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_brand_rules_workspace_brand",
        "brand_rules",
        ["workspace_id", "brand_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("brand_rules")
    op.drop_table("brand_profiles")
