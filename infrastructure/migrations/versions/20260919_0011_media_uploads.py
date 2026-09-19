"""Allow media uploads before campaign assignment.

Revision ID: 20260919_0011
Revises: 20260918_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_0011"
down_revision: str | None = "20260918_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("media_assets", "campaign_id", existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    op.alter_column("media_assets", "campaign_id", existing_type=sa.Uuid(), nullable=False)
