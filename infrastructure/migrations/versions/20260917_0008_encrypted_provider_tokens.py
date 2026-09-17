"""Reserve sufficient storage for encrypted provider-token envelopes.

Revision ID: 20260917_0008
Revises: 20260916_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260917_0008"
down_revision: str | None = "20260916_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("social_accounts") as batch_op:
        batch_op.alter_column(
            "access_token_ref",
            existing_type=sa.String(length=512),
            type_=sa.String(length=2048),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("social_accounts") as batch_op:
        batch_op.alter_column(
            "access_token_ref",
            existing_type=sa.String(length=2048),
            type_=sa.String(length=512),
            existing_nullable=False,
        )
