"""Create legacy feedback aggregation view

Revision ID: 20241120_feedback
Revises:
Create Date: 2024-11-20 00:00:00
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20241120_feedback"
down_revision = None
branch_labels = None
depends_on = None


CREATE_VIEW_SQL = """
CREATE OR REPLACE VIEW legacy_feedback_view AS
SELECT
    ul.user_id,
    CASE
        WHEN ul.submission_status IS NULL THEN FALSE
        WHEN ul.submission_status = '' THEN FALSE
        WHEN LOWER(ul.submission_status) = 'not_submitted' THEN FALSE
        ELSE TRUE
    END AS submission_status,
    COALESCE(ea.accepted_1, FALSE) AS task_1_accepted,
    COALESCE(ea.accepted_2, FALSE) AS task_2_accepted,
    COALESCE(ea.accepted_3, FALSE) AS task_3_accepted,
    CASE
        WHEN COALESCE(ul.approved, 0) > 0 THEN TRUE
        ELSE FALSE
    END AS interview_approved,
    ul.task_1_feedback,
    ul.task_2_feedback,
    ul.task_3_feedback,
    ul.interview_feedback
FROM users_legacy ul
LEFT JOIN evaluated_applications ea ON ea.user_id = ul.user_id;
"""

DROP_VIEW_SQL = "DROP VIEW IF EXISTS legacy_feedback_view;"


def upgrade() -> None:
    op.execute(CREATE_VIEW_SQL)


def downgrade() -> None:
    op.execute(DROP_VIEW_SQL)
