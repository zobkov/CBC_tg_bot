"""Create lectory_questions table for Q&A feature

Revision ID: 20260411_lectory_questions
Revises: 20260411_career_fair_events
Create Date: 2026-04-11 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260411_lectory_questions"
down_revision: Union[str, Sequence[str], None] = "20260411_career_fair_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lectory_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_key", sa.String(length=64), nullable=False),
        sa.Column("event_name", sa.String(length=256), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
    )
    op.create_index("idx_lq_user_id", "lectory_questions", ["user_id"])
    op.create_index("idx_lq_event_key", "lectory_questions", ["event_key"])


def downgrade() -> None:
    op.drop_index("idx_lq_event_key", table_name="lectory_questions")
    op.drop_index("idx_lq_user_id", table_name="lectory_questions")
    op.drop_table("lectory_questions")
