"""Create user_info table

Revision ID: 20260114_create_user_info
Revises: 20241120_feedback_view
Create Date: 2026-01-14 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260114_create_user_info"
down_revision = "20241120_feedback_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_info table with explicit FK to users.user_id.
    op.create_table(
        "user_info",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
        sa.Column(
            "updated",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("university_course", sa.Text(), nullable=True),
        sa.Column("occupation", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_user_info_user_id"),
    )

def downgrade() -> None:
    op.drop_table("user_info")
