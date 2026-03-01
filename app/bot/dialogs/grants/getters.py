"""Data getters for the grants dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB
from app.services.grant_lessons_config import load_grant_lessons, get_lesson_by_tag

logger = logging.getLogger(__name__)

_TOTAL_LESSONS = 11


async def get_mentor_data(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Build data for the MENTOR window."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    user_id = event_from_user.id

    lessons = load_grant_lessons()
    approved_tags: list[str] = []
    mentor_contacts = "Не назначен"

    if db:
        try:
            record = await db.user_mentors.get_by_user_id(user_id=user_id)
            if record:
                approved_tags = record.lessons_approved or []
                mentor_contacts = record.mentor_contacts or "Не назначен"
        except Exception as exc:  # noqa: BLE001
            logger.error("get_mentor_data: DB error for user %d: %s", user_id, exc)

    approved_set = set(approved_tags)

    # Formatted list for the window text
    lines: list[str] = []
    for lesson in lessons:
        tag = lesson.get("tag", "")
        name = lesson.get("name", tag)
        status = "✅" if tag in approved_set else "🔒"
        lines.append(f"{status} {name}")
    lessons_list = "\n".join(lines)

    # Buttons are only shown for unlocked lessons
    open_lessons = [
        (lesson["name"], lesson["tag"])
        for lesson in lessons
        if lesson.get("tag") in approved_set
    ]

    return {
        "num_open_lessons": len(approved_tags),
        "total_lessons": _TOTAL_LESSONS,
        "mentor_contacts": mentor_contacts,
        "lessons_list": lessons_list,
        "open_lessons": open_lessons,
    }


async def get_lesson_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Build data for the LESSON window from dialog_data."""
    tag = dialog_manager.dialog_data.get("selected_lesson_tag", "")
    lesson = get_lesson_by_tag(tag)

    if not lesson:
        logger.warning("get_lesson_data: lesson not found for tag '%s'", tag)
        return {
            "lesson_name": "Урок не найден",
            "lesson_description": "",
            "lesson_url": "https://ya.ru",
        }

    return {
        "lesson_name": lesson.get("name", ""),
        "lesson_description": lesson.get("description", ""),
        "lesson_url": lesson.get("url") or "https://ya.ru",
    }
