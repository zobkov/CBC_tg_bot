"""Add phone column to user_info table

Revision ID: 20260307_add_phone_to_user_info
Revises: 20260307_create_volunteer_apps
Create Date: 2026-03-07
"""
from alembic import op
import sqlalchemy as sa

revision = "20260307_add_phone_to_user_info"
down_revision = "20260307_create_volunteer_apps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_info",
        sa.Column("phone", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_info", "phone")
