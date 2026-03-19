"""Add reviewed column to volunteer_selection_part2

Revision ID: 20260318_vol_sel_p2_reviewed
Revises: 20260318_vol_sel_part2
Create Date: 2026-03-18 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260318_vol_sel_p2_reviewed"
down_revision = "20260318_vol_sel_part2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "volunteer_selection_part2",
        sa.Column(
            "reviewed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("volunteer_selection_part2", "reviewed")
