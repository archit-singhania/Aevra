"""Add one-time OAuth states and refresh-token metadata.

Revision ID: 20260918_0010
Revises: 20260917_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_0010"
down_revision: str | None = "20260917_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nonce_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nonce_hash", name="uq_oauth_states_nonce_hash"),
    )
    op.create_index(
        "ix_oauth_states_expires", "oauth_states", ["expires_at", "consumed_at"]
    )
    op.create_index("ix_oauth_states_user_id", "oauth_states", ["user_id"])
    op.create_index("ix_oauth_states_workspace_id", "oauth_states", ["workspace_id"])
    with op.batch_alter_table("social_accounts") as batch_op:
        batch_op.add_column(
            sa.Column("refresh_token_ref", sa.String(length=2048), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "access_token_expires_at", sa.DateTime(timezone=True), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column(
                "granted_scopes",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("social_accounts") as batch_op:
        batch_op.drop_column("granted_scopes")
        batch_op.drop_column("access_token_expires_at")
        batch_op.drop_column("refresh_token_ref")
    op.drop_index("ix_oauth_states_workspace_id", table_name="oauth_states")
    op.drop_index("ix_oauth_states_user_id", table_name="oauth_states")
    op.drop_index("ix_oauth_states_expires", table_name="oauth_states")
    op.drop_table("oauth_states")
