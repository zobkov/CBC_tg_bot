"""Legacy feedback view placeholder merge

Revision ID: 20241120_feedback_view
Revises: 20241120_feedback
Create Date: 2024-11-20 00:05:00
"""
from __future__ import annotations


# revision identifiers, used by Alembic.
revision = "20241120_feedback_view"
down_revision = "20241120_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Nothing to do; keeps history linear after renaming revision."""


def downgrade() -> None:
    """Nothing to revert."""
