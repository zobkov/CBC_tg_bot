"""Create bot_forum_registrations table

Revision ID: 20260312_bot_forum_regs
Revises: 20260310_vol_per_role_add_info
Create Date: 2026-03-12 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260312_bot_forum_regs"
down_revision = "20260310_vol_per_role_add_info"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bot_forum_registrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Soft reference to site_registrations.id (UUID string, managed by external app)
        sa.Column("unique_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("adult18", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("occupation_status", sa.Text(), nullable=True),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("track", sa.Text(), nullable=True),
        sa.Column("transport", sa.Text(), nullable=True),
        sa.Column("car_number", sa.Text(), nullable=True),
        sa.Column("passport", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.UniqueConstraint("user_id", name="uq_bot_forum_regs_user_id"),
        sa.UniqueConstraint("unique_id", name="uq_bot_forum_regs_unique_id"),
    )
    op.create_index(
        "idx_bot_forum_regs_user_id",
        "bot_forum_registrations",
        ["user_id"],
    )
    op.create_index(
        "idx_bot_forum_regs_unique_id",
        "bot_forum_registrations",
        ["unique_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_bot_forum_regs_unique_id", table_name="bot_forum_registrations")
    op.drop_index("idx_bot_forum_regs_user_id", table_name="bot_forum_registrations")
    op.drop_table("bot_forum_registrations")
