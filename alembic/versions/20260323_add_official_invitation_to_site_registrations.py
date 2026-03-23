"""add official_invitation to site_registrations

Revision ID: 20260323_0006
Revises: 20260318_0005
Create Date: 2026-03-23 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260323_invitation"
down_revision: Union[str, Sequence[str], None] = "20260318_increase_300"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_registrations",
        sa.Column("official_invitation", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("site_registrations", "official_invitation")
