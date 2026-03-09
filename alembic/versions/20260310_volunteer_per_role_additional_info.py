"""Add per-role additional_information columns to volunteer_applications

Revision ID: 20260310_vol_per_role_add_info
Revises: 20260307_create_volunteer_apps
Create Date: 2026-03-10 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260310_vol_per_role_add_info"
down_revision = "20260307_add_phone_to_user_info"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "volunteer_applications",
        sa.Column("general_additional_information", sa.Text(), nullable=True),
    )
    op.add_column(
        "volunteer_applications",
        sa.Column("photo_additional_information", sa.Text(), nullable=True),
    )
    op.add_column(
        "volunteer_applications",
        sa.Column("translate_additional_information", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("volunteer_applications", "translate_additional_information")
    op.drop_column("volunteer_applications", "photo_additional_information")
    op.drop_column("volunteer_applications", "general_additional_information")
