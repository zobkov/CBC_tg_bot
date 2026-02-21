"""Create online_events and online_registrations tables

Revision ID: 20260219_create_online_lectures
Revises: 20260213_create_creative_apps
Create Date: 2026-02-19 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260219_create_online_lectures"
down_revision = "20260213_create_creative_apps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "online_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("alias", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("speaker", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column(
            "start_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "end_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
    )

    op.create_table(
        "online_registrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("online_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "registered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )

    # Index for querying active registrations
    op.create_index(
        "idx_registrations_active",
        "online_registrations",
        ["event_id"],
        postgresql_where=sa.text("status = 'active'"),
    )

    # Index for querying upcoming events
    op.create_index(
        "idx_events_upcoming",
        "online_events",
        ["start_at"],
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("idx_events_upcoming", table_name="online_events")
    op.drop_index("idx_registrations_active", table_name="online_registrations")
    op.drop_table("online_registrations")
    op.drop_table("online_events")
