"""Getter helpers for the guest feedback dialogs."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from aiogram.types import User
from aiogram_dialog import DialogManager

from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.feedback import FeedbackModel

LOGGER = logging.getLogger(__name__)


async def _fetch_feedback_model(dialog_manager: DialogManager) -> FeedbackModel | None:
    """Safely load the feedback model for the current user."""

    user: User = dialog_manager.event.from_user
    db: DB | None = dialog_manager.middleware_data.get("db")

    if db is None:
        LOGGER.debug(
            "Feedback dialog skipped: database facade is missing for user %s",
            user.id,
        )
        return None

    try:
        return await db.feedback.get_user_feedback(user_id=user.id)
    except (SQLAlchemyError, AttributeError) as exc:  # pragma: no cover
        LOGGER.error("Failed to load feedback for user %s: %s", user.id, exc)
        return None


async def get_tasks_feedback_menu(dialog_manager: DialogManager, **_: Any) -> Dict[str, Any]:
    """Expose the list of available task feedback entries."""

    feedback_model = await _fetch_feedback_model(dialog_manager)

    tasks: List[Dict[str, Any]] = []
    if feedback_model and feedback_model.can_show_tasks_feedback():
        for idx, text in feedback_model.iter_task_feedback():
            tasks.append(
                {
                    "task_id": str(idx),
                    "title": f"Задание {idx}",
                    "text": text,
                }
            )

    dialog_manager.dialog_data["tasks_cache"] = tasks

    return {
        "has_task_feedback": bool(tasks),
        "tasks": tasks,
    }


async def get_task_feedback_details(dialog_manager: DialogManager, **_: Any) -> Dict[str, Any]:
    """Return the text for the task currently selected in dialog data."""

    selected = dialog_manager.dialog_data.get("selected_task")
    if not selected:
        return {
            "task_title": "Задание",
            "task_feedback_text": "Обратная связь недоступна.",
        }

    return {
        "task_title": selected.get("title", "Задание"),
        "task_feedback_text": selected.get("text", "Обратная связь недоступна."),
    }


async def get_interview_feedback(dialog_manager: DialogManager, **_: Any) -> Dict[str, Any]:
    """Provide interview feedback text with an availability flag."""

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
