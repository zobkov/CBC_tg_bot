"""Data getters used across the guest dialogs."""

from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any

from aiogram.enums import ContentType
from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.dao.feedback import FeedbackDAO
from app.infrastructure.database.dao.interview import InterviewDAO
from app.infrastructure.database.database.db import DB
from app.utils.deadline_checker import is_task_submission_closed
from app.utils.optimized_dialog_widgets import get_file_id_for_path
from config.config import Config, load_config

LOGGER = logging.getLogger(__name__)

def _get_config(dialog_manager: DialogManager) -> Config | None:
    config: Config | None = dialog_manager.middleware_data.get("config")
    if config:
        return config

    dispatcher = (
        dialog_manager.middleware_data.get("_dispatcher")
        or dialog_manager.middleware_data.get("dispatcher")
        or dialog_manager.middleware_data.get("dp")
    )
    if dispatcher:
        config = dispatcher.get("config")
        if config:
            return config

    return load_config()


async def get_user_info(
    _dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return a subset of Telegram user data for templates."""

    return {
        "user_id": event_from_user.id,
        "username": event_from_user.username or "",
        "first_name": event_from_user.first_name or "",
        "last_name": event_from_user.last_name or "",
    }


async def get_support_contacts(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Expose support contacts configured in settings."""

    config = dialog_manager.middleware_data.get("config") or _get_config(dialog_manager)
    if not config:
        return {
            "general_support": "Недоступно",
            "technical_support": "Недоступно",
            "hr_support": "Недоступно",
        }

    contacts = config.selection.support_contacts
    return {
        "general_support": contacts["general"],
        "technical_support": contacts["technical"],
        "hr_support": contacts["hr"],
    }


async def get_main_menu_media(
    **_kwargs: Any,
) -> dict[str, Any]:
    """Load photo attachment definition for the guest main menu."""

    file_id = get_file_id_for_path("main_menu/main_menu.jpg")
    if file_id:
        media = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path="app/bot/assets/images/main_menu/main_menu.jpg",
        )

    return {"media": media}


async def get_interview_feedback(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return interview feedback text if available."""

    db = _get_db(dialog_manager)
    user = _get_user(dialog_manager)

    if not db:
        return {
            "interview_feedback": DEFAULT_INTERVIEW_FEEDBACK,
            "has_interview_feedback": False,
        }

    try:
        feedback_model = await db.feedback.get_user_feedback(user_id=user.id)
    except (SQLAlchemyError, AttributeError) as exc:
        LOGGER.error("Failed to fetch interview feedback for %s: %s", user.id, exc)
        feedback_model = None

    if feedback_model and feedback_model.can_show_interview_feedback():
        feedback_text = (
            feedback_model.interview_feedback or ""
        ).strip() or DEFAULT_INTERVIEW_FEEDBACK
        return {
            "interview_feedback": feedback_text,
            "has_interview_feedback": True,
        }

    return {
        "interview_feedback": DEFAULT_INTERVIEW_FEEDBACK,
        "has_interview_feedback": False,
    }
