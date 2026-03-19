"""Create volunteer_selection_part2 table

Revision ID: 20260318_vol_sel_part2
Revises: 20260318_increase_300
Create Date: 2026-03-18 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260318_vol_sel_part2"
down_revision = "20260318_increase_300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "volunteer_selection_part2",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Written questions
        sa.Column("q1_kbc_ordinal", sa.Text(), nullable=True),
        sa.Column("q2_kbc_date", sa.Text(), nullable=True),
        sa.Column("q3_kbc_theme", sa.Text(), nullable=True),
        sa.Column("q4_team_experience", sa.Text(), nullable=True),
        sa.Column("q5_badge_case", sa.Text(), nullable=True),
        sa.Column("q6_foreign_guest_case", sa.Text(), nullable=True),
        sa.Column("q7_want_tour", sa.Text(), nullable=True),         # "yes" | "no"
        sa.Column("q7_has_tour_experience", sa.Text(), nullable=True),  # "yes" | "no"
        sa.Column("q7_tour_route", sa.Text(), nullable=True),
        # Video interview file_ids
        sa.Column("vq1_file_id", sa.Text(), nullable=True),
        sa.Column("vq2_file_id", sa.Text(), nullable=True),
        sa.Column("vq3_file_id", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("user_id", name="uq_vol_sel_part2_user_id"),
    )
    op.create_index(
        "idx_vol_sel_part2_user_id",
        "volunteer_selection_part2",
        ["user_id"],
    )
    op.execute(
        """
CREATE OR REPLACE FUNCTION set_updated_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_set_vol_sel_part2_updated
BEFORE UPDATE ON volunteer_selection_part2
FOR EACH ROW EXECUTE FUNCTION set_updated_timestamp();
"""
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_set_vol_sel_part2_updated ON volunteer_selection_part2;"
    )
    op.drop_index("idx_vol_sel_part2_user_id", table_name="volunteer_selection_part2")
    op.drop_table("volunteer_selection_part2")
