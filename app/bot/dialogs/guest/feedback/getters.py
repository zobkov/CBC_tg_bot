from __future__ import annotations

import logging
from typing import Any, Dict

from aiogram.types import User
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.feedback import FeedbackModel

logger = logging.getLogger(__name__)


async def _fetch_feedback_model(dialog_manager: DialogManager) -> FeedbackModel | None:
    user: User = dialog_manager.event.from_user
    db: DB | None = dialog_manager.middleware_data.get("db")

    if db is None:
        logger.debug("Feedback dialog skipped: database facade is missing for user %s", user.id)
        return None

    try:
        return await db.feedback.get_user_feedback(user_id=user.id)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to load feedback for user %s: %s", user.id, exc)
        return None


async def get_tasks_feedback(dialog_manager: DialogManager, **_: Any) -> Dict[str, Any]:
    feedback_model = await _fetch_feedback_model(dialog_manager)

    if feedback_model and feedback_model.can_show_tasks_feedback():
        parts: list[str] = []
        for idx, text in feedback_model.iter_task_feedback():
            parts.append(f"<b>Задание {idx}:</b>\n{text}")
        feedback_text = "\n\n".join(parts)
        has_feedback = True
    else:
        feedback_text = "Обратная связь по тестовым заданиям недоступна."
        has_feedback = False

    return {
        "has_task_feedback": has_feedback,
        "task_feedback_text": feedback_text,
    }


async def get_interview_feedback(dialog_manager: DialogManager, **_: Any) -> Dict[str, Any]:
    feedback_model = await _fetch_feedback_model(dialog_manager)

    if feedback_model and feedback_model.can_show_interview_feedback():
        message_text = (feedback_model.interview_feedback or "").strip()
        has_feedback = True
    else:
        message_text = "Обратная связь по собеседованию недоступна."
        has_feedback = False

    return {
        "has_interview_feedback": has_feedback,
        "interview_feedback_text": message_text,
    }
