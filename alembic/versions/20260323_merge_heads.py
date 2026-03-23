"""merge heads

Revision ID: 20260323_merge
Revises: 20260318_vol_sel_p2_reviewed, 20260323_invitation
Create Date: 2026-03-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260323_merge"
down_revision: Union[str, Sequence[str], None] = (
    "20260318_vol_sel_p2_reviewed",
    "20260323_invitation",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
