"""increase full_name, region, education columns to 300 chars

Revision ID: 20260318_0005
Revises: 20260313_0004
Create Date: 2026-03-18 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260318_increase_300"
down_revision: Union[str, Sequence[str], None] = "20260312_bot_forum_regs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "site_registrations", "full_name",
        existing_type=sa.String(length=200),
        type_=sa.String(length=300),
        nullable=False,
    )
    op.alter_column(
        "site_registrations", "region",
        existing_type=sa.String(length=120),
        type_=sa.String(length=300),
        nullable=True,
    )
    op.alter_column(
        "site_registrations", "education",
        existing_type=sa.String(length=120),
        type_=sa.String(length=300),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "site_registrations", "education",
        existing_type=sa.String(length=300),
        type_=sa.String(length=120),
        nullable=True,
    )
    op.alter_column(
        "site_registrations", "region",
        existing_type=sa.String(length=300),
        type_=sa.String(length=120),
        nullable=True,
    )
    op.alter_column(
        "site_registrations", "full_name",
        existing_type=sa.String(length=300),
        type_=sa.String(length=200),
        nullable=False,
    )
