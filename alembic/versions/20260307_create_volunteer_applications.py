"""Create volunteer_applications table

Revision ID: 20260307_create_volunteer_apps
Revises: 20260302_creative_part2
Create Date: 2026-03-07 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260307_create_volunteer_apps"
down_revision = "20260302_creative_part2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "volunteer_applications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Compulsory fields
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("volunteer_dates", sa.Text(), nullable=True),  # "single" | "double"
        sa.Column("function", sa.Text(), nullable=True),  # "general" | "photo" | "translate"
        # General branch
        sa.Column("general_1_type", sa.Text(), nullable=True),  # "guest" | "volunteer" | "guest_and_volunteer" | "no"
        sa.Column("general_1_answer", sa.Text(), nullable=True),
        sa.Column("general_2", sa.Text(), nullable=True),
        sa.Column("general_3", sa.Text(), nullable=True),
        # Photo branch
        sa.Column("photo_portfolio", sa.Text(), nullable=True),
        sa.Column("photo_has_equipment", sa.Text(), nullable=True),  # "yes" | "no"
        sa.Column("photo_experience", sa.Text(), nullable=True),
        sa.Column("photo_key_moments", sa.Text(), nullable=True),
        # Translation branch
        sa.Column("translate_level", sa.Text(), nullable=True),
        sa.Column("translate_has_cert", sa.Text(), nullable=True),  # "yes" | "no"
        sa.Column("translate_cert_link", sa.Text(), nullable=True),
        sa.Column("translate_experience_detail", sa.Text(), nullable=True),
        sa.Column("translate_worked_with_foreigners", sa.Text(), nullable=True),
        sa.Column("translate_difficult_situation", sa.Text(), nullable=True),
        # Additional info
        sa.Column("additional_information", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "submitted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.Column(
            "updated",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.UniqueConstraint("user_id", name="uq_volunteer_apps_user_id"),
    )
    op.create_index(
        "idx_volunteer_apps_user_id",
        "volunteer_applications",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_volunteer_apps_user_id", table_name="volunteer_applications")
    op.drop_table("volunteer_applications")
