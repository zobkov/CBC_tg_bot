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
    # Create table without forcing a foreign key; attempt to add FK only if
    # the referenced column on `users` is unique/primary to avoid failing
    # migrations on databases with legacy schema differences.
    op.create_table(
        "user_info",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
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

    # Try to add foreign key constraint only if `users.user_id` is a primary
    # key or has a unique constraint. This keeps the migration safe for
    # environments where `users` was created differently.
    op.execute(
        """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
        WHERE t.relname='users'
          AND a.attname='user_id'
          AND c.contype IN ('p', 'u')
    ) THEN
        ALTER TABLE user_info
        ADD CONSTRAINT fk_user_info_user_id FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE;
    END IF;
END $$;
""",
    )


def downgrade() -> None:
    op.drop_table("user_info")
