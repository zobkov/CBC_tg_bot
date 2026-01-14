"""Create broadcasts and user_subscriptions tables

Revision ID: 20260114_create_broadcasts_subs
Revises: 20260114_mig_apps_userinfo
Create Date: 2026-01-14 02:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260114_create_broadcasts_subs"
down_revision = "20260114_mig_apps_userinfo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.UniqueConstraint("key", name="uq_broadcasts_key"),
    )

    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "broadcast_id",
            sa.Integer(),
            sa.ForeignKey("broadcasts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscribed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.Column("unsubscribed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.UniqueConstraint("user_id", "broadcast_id", name="uq_user_broadcast"),
    )

    # Partial index for active subscriptions
    op.create_index(
        "idx_subs_active",
        "user_subscriptions",
        ["broadcast_id"],
        postgresql_where=sa.text("unsubscribed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_subs_active", table_name="user_subscriptions")
    op.drop_table("user_subscriptions")
    op.drop_table("broadcasts")
