"""Create creative_applications table

Revision ID: 20260213_create_creative_apps
Revises: 20260114_create_broadcasts_subs
Create Date: 2026-02-13 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "20260213_create_creative_apps"
down_revision = "20260114_create_broadcasts_subs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create creative_applications table
    op.create_table(
        "creative_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("contact", sa.Text(), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        # Ceremony branch fields
        sa.Column("ceremony_stage_experience", sa.Text(), nullable=True),
        sa.Column("ceremony_motivation", sa.Text(), nullable=True),
        sa.Column("ceremony_can_attend_md", sa.Boolean(), nullable=True),
        sa.Column("ceremony_rehearsal_frequency", sa.Text(), nullable=True),
        sa.Column("ceremony_rehearsal_duration", sa.Text(), nullable=True),
        sa.Column("ceremony_timeslots", JSONB, nullable=True),
        sa.Column("ceremony_cloud_link", sa.Text(), nullable=True),
        # Fair branch fields
        sa.Column("fair_roles", JSONB, nullable=True),
        sa.Column("fair_motivation", sa.Text(), nullable=True),
        sa.Column("fair_experience", sa.Text(), nullable=True),
        sa.Column("fair_cloud_link", sa.Text(), nullable=True),
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
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("user_id", name="uq_creative_apps_user_id"),
    )

    # Create index on user_id for efficient queries
    op.create_index(
        "idx_creative_apps_user_id",
        "creative_applications",
        ["user_id"],
    )

    # Create index on direction for filtering
    op.create_index(
        "idx_creative_apps_direction",
        "creative_applications",
        ["direction"],
    )

    # Ensure trigger function exists (may already exist from other tables)
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

    # Attach trigger to creative_applications
    op.execute(
        """
CREATE TRIGGER trg_set_creative_apps_updated
BEFORE UPDATE ON creative_applications
FOR EACH ROW EXECUTE FUNCTION set_updated_timestamp();
"""
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_set_creative_apps_updated ON creative_applications;")
    op.drop_index("idx_creative_apps_direction", table_name="creative_applications")
    op.drop_index("idx_creative_apps_user_id", table_name="creative_applications")
    op.drop_table("creative_applications")
