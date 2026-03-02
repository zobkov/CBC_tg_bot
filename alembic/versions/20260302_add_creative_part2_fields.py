"""Add part2 answer fields to creative_applications

Revision ID: 20260302_add_creative_part2_fields
Revises: 20260213_create_creative_apps
Create Date: 2026-03-02 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260302_creative_part2"
down_revision = "20260219_create_online_lectures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Open questions (block 1)
    op.add_column("creative_applications", sa.Column("part2_open_q1", sa.Text(), nullable=True))
    op.add_column("creative_applications", sa.Column("part2_open_q2", sa.Text(), nullable=True))
    op.add_column("creative_applications", sa.Column("part2_open_q3", sa.Text(), nullable=True))
    # Case questions (block 2)
    op.add_column("creative_applications", sa.Column("part2_case_q1", sa.Text(), nullable=True))
    op.add_column("creative_applications", sa.Column("part2_case_q2", sa.Text(), nullable=True))
    op.add_column("creative_applications", sa.Column("part2_case_q3", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("creative_applications", "part2_case_q3")
    op.drop_column("creative_applications", "part2_case_q2")
    op.drop_column("creative_applications", "part2_case_q1")
    op.drop_column("creative_applications", "part2_open_q3")
    op.drop_column("creative_applications", "part2_open_q2")
    op.drop_column("creative_applications", "part2_open_q1")
