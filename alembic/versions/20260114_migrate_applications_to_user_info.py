"""Migrate relevant rows from applications into user_info

Revision ID: 20260114_mig_apps_userinfo
Revises: 20260114_upd_user_info
Create Date: 2026-01-14 01:45:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import re

# revision identifiers, used by Alembic.
revision = "20260114_mig_apps_userinfo"
down_revision = "20260114_upd_user_info"
branch_labels = None
depends_on = None


def _parse_education_and_course(university: str) -> tuple[str | None, str | None]:
    if not university:
        return None, None
    parts = [p.strip() for p in university.split(",") if p.strip()]
    education = None
    course = None
    if parts:
        education = ", ".join(parts[:2]) if len(parts) >= 2 else parts[0]
        # find last numeric token (year or course number)
        nums = re.findall(r"(\d{2,4})", university)
        if nums:
            course = nums[-1]
    return education, course


def upgrade() -> None:
    conn = op.get_bind()

    # Detect whether `telegram_username` or `username` column exists in `applications`
    col_check_telegram = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns WHERE table_name = 'applications' AND column_name = 'telegram_username' LIMIT 1"
        )
    ).fetchone()
    col_check_username = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns WHERE table_name = 'applications' AND column_name = 'username' LIMIT 1"
        )
    ).fetchone()

    username_col = None
    if col_check_telegram:
        username_col = "telegram_username"
    elif col_check_username:
        username_col = "username"

    has_username = username_col is not None

    select_cols = ["user_id", "full_name", "email", "university"]
    if has_username:
        select_cols.insert(3, username_col)

    select_sql = text(
        "SELECT " + ", ".join(select_cols) + " FROM applications WHERE full_name IS NOT NULL AND trim(full_name) <> ''"
    )

    results = conn.execute(select_sql).fetchall()

    if not results:
        # nothing to migrate
        return

    # Build insert/upsert SQL dynamically depending on availability of `username`
    if has_username:
        insert_sql = text(
            """
INSERT INTO user_info (user_id, created, updated, full_name, email, username, education, university_course, occupation)
VALUES (:user_id, NOW(), NOW(), :full_name, :email, :username, :education, :university_course, NULL)
ON CONFLICT (user_id) DO UPDATE
SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    username = EXCLUDED.username,
    education = EXCLUDED.education,
    university_course = EXCLUDED.university_course,
    updated = NOW();
"""
        )
        for row in results:
            # ordering of columns: user_id, full_name, email, <username_col>, university
            user_id, full_name, email, username, university = row
            education, university_course = _parse_education_and_course(university)

            conn.execute(
                insert_sql,
                {
                    "user_id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "username": username,
                    "education": education,
                    "university_course": university_course,
                },
            )
    else:
        insert_sql = text(
            """
INSERT INTO user_info (user_id, created, updated, full_name, email, education, university_course, occupation)
VALUES (:user_id, NOW(), NOW(), :full_name, :email, :education, :university_course, NULL)
ON CONFLICT (user_id) DO UPDATE
SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    education = EXCLUDED.education,
    university_course = EXCLUDED.university_course,
    updated = NOW();
"""
        )

        for row in results:
            user_id, full_name, email, university = row
            education, university_course = _parse_education_and_course(university)

            conn.execute(
                insert_sql,
                {
                    "user_id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "education": education,
                    "university_course": university_course,
                },
            )


def downgrade() -> None:
    # No-op downgrade: data migrations are not reversed automatically.
    pass
