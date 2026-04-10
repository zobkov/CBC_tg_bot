"""Create career_fair_events table for analytics

Revision ID: 20260411_career_fair_events
Revises: 20260323_merge
Create Date: 2026-04-11 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260411_career_fair_events"
down_revision: Union[str, Sequence[str], None] = "20260323_merge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_fair_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("track_key", sa.String(length=64), nullable=True),
        sa.Column("company_key", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
    )
    op.create_index("idx_cfe_user_id", "career_fair_events", ["user_id"])
    op.create_index("idx_cfe_event_type", "career_fair_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("idx_cfe_event_type", table_name="career_fair_events")
    op.drop_index("idx_cfe_user_id", table_name="career_fair_events")
    op.drop_table("career_fair_events")
