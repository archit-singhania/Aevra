"""Add tenant onboarding payment gate and admin approval."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_0012"
down_revision: str | None = "20260919_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "account_status",
                sa.String(24),
                nullable=False,
                server_default="approved",
            )
        )
        batch.add_column(
            sa.Column(
                "payment_required",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch.add_column(sa.Column("approved_by", sa.Uuid(), nullable=True))
        batch.add_column(
            sa.Column(
                "is_admin", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch.create_index("ix_users_account_status", ["account_status"])
        batch.create_foreign_key(
            "fk_users_approved_by", "users", ["approved_by"], ["id"]
        )
    op.create_table(
        "payment_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.String(32), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("upi_id_snapshot", sa.String(320), nullable=False, server_default=""),
        sa.Column("utr_reference", sa.String(128), nullable=True),
        sa.Column("proof_asset_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(24), nullable=False, server_default="pending_payment"
        ),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_submissions_status", "payment_submissions", ["status"])
    op.create_index(
        "ix_payment_submissions_user_id", "payment_submissions", ["user_id"]
    )
    op.create_index(
        "ix_payment_submissions_tenant_id", "payment_submissions", ["tenant_id"]
    )


def downgrade() -> None:
    op.drop_table("payment_submissions")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_approved_by", type_="foreignkey")
        batch.drop_index("ix_users_account_status")
        for name in (
            "is_admin",
            "approved_by",
            "approved_at",
            "payment_required",
            "account_status",
        ):
            batch.drop_column(name)
