"""Add updated column to users and trigger

Revision ID: 20260114_add_updated_column_to_users
Revises: 20260114_fix_pk_fk
Create Date: 2026-01-14 01:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
# Short revision id to fit alembic_version column length
revision = "20260114_upd_users"
down_revision = "20260114_fix_pk_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add `updated` column with timezone-aware timestamp and default
    op.add_column(
        "users",
        sa.Column(
            "updated",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Backfill `updated` from `created` where appropriate
    op.execute(
        "UPDATE users SET updated = created WHERE created IS NOT NULL AND (updated IS NULL OR updated = NOW());"
    )

    # Create a function to auto-update `updated` timestamp on UPDATE
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

    # Attach trigger to users table
    op.execute(
        "CREATE TRIGGER trg_set_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_timestamp();"
    )


def downgrade() -> None:
    # Remove trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_set_users_updated ON users;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_timestamp();")

    # Drop the column
    op.drop_column("users", "updated")
