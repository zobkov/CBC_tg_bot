"""Ensure users.user_id is primary key and add FK from user_info

Revision ID: 20260114_fix_pk_fk
Revises: 20260114_create_user_info
Create Date: 2026-01-14 00:30:00
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260114_fix_pk_fk"
down_revision = "20260114_create_user_info"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure users.user_id is primary key (no-op if already primary key)
    op.execute(
        """
DO $$
BEGIN
    -- If users has no primary key, try to add one on user_id
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'users'::regclass
          AND c.contype = 'p'
    ) THEN
        ALTER TABLE users
        ADD PRIMARY KEY (user_id);
    END IF;
END $$;
""",
    )

    # Add FK constraint from user_info.user_id -> users.user_id if missing
    op.execute(
        """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_user_info_user_id'
    ) THEN
        ALTER TABLE user_info
        ADD CONSTRAINT fk_user_info_user_id FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE;
    END IF;
END $$;
""",
    )


def downgrade() -> None:
    # Remove FK if present
    op.execute("ALTER TABLE user_info DROP CONSTRAINT IF EXISTS fk_user_info_user_id;")

    # Remove primary key on users if it was added by this migration
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;")
