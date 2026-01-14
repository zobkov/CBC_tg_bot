"""Add updated column and trigger to user_info

Revision ID: 20260114_add_updated_to_user_info
Revises: 20260114_add_updated_column_to_users
Create Date: 2026-01-14 01:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260114_upd_user_info"
down_revision = "20260114_upd_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add `updated` column to user_info if it does not exist (safe on existing DBs)
    op.execute(
        "ALTER TABLE user_info ADD COLUMN IF NOT EXISTS updated TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;"
    )

    # Backfill `updated` from `created` where applicable
    op.execute(
        "UPDATE user_info SET updated = created WHERE created IS NOT NULL AND (updated IS NULL OR updated = NOW());"
    )

    # Ensure trigger function exists (re-use or replace existing)
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

    # Attach trigger to user_info (create only if missing)
    op.execute(
        """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_set_user_info_updated'
    ) THEN
        CREATE TRIGGER trg_set_user_info_updated
        BEFORE UPDATE ON user_info
        FOR EACH ROW EXECUTE FUNCTION set_updated_timestamp();
    END IF;
END $$;
"""
    )


def downgrade() -> None:
    # Remove trigger and column
    op.execute("DROP TRIGGER IF EXISTS trg_set_user_info_updated ON user_info;")
    op.drop_column("user_info", "updated")
