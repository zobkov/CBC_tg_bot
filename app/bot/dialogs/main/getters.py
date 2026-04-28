"""Data getters used across the main dialogs."""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from aiogram.enums import ContentType
from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.dao.feedback import FeedbackDAO
from app.infrastructure.database.dao.interview import InterviewDAO
from app.infrastructure.database.database.db import DB
from app.services.participant_cert import is_cert_eligible
from app.utils.deadline_checker import is_task_submission_closed
from app.utils.optimized_dialog_widgets import get_file_id_for_path
from config.config import Config, load_config

LOGGER = logging.getLogger(__name__)

# Load fair CSV user IDs once at import time (no header row, one user_id per line)
_FAIR_CSV_PATH = Path("export_fair.csv")
try:
    with _FAIR_CSV_PATH.open(newline="") as _f:
        _FAIR_USER_IDS: frozenset[int] = frozenset(
            int(row[0]) for row in csv.reader(_f) if row and row[0].strip().isdigit()
        )
    LOGGER.info("Loaded %d fair user IDs from %s", len(_FAIR_USER_IDS), _FAIR_CSV_PATH)
except FileNotFoundError:
    _FAIR_USER_IDS = frozenset()
    LOGGER.warning("export_fair.csv not found — casting button hidden for all non-admins")

# Load vol general passed CSV user IDs once at import time
_VOL_GENERAL_PASSED_CSV_PATH = Path("КБК 26 Отбор волонтеров - общ_рассылка_прошли.csv")
try:
    with _VOL_GENERAL_PASSED_CSV_PATH.open(newline="", encoding="utf-8") as _f:
        _VOL_GENERAL_PASSED_IDS: frozenset[int] = frozenset(
            int(row[0]) for row in csv.reader(_f) if row and row[0].strip().isdigit()
        )
    LOGGER.info(
        "Loaded %d vol general passed user IDs from %s",
        len(_VOL_GENERAL_PASSED_IDS),
        _VOL_GENERAL_PASSED_CSV_PATH,
    )
except FileNotFoundError:
    _VOL_GENERAL_PASSED_IDS = frozenset()
    LOGGER.warning("%s not found — vol part2 button hidden for all non-admins", _VOL_GENERAL_PASSED_CSV_PATH)


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


async def get_is_admin(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return whether the current user is in the admin_ids list from config."""
    config = dialog_manager.middleware_data.get("config") or _get_config(dialog_manager)
    if config is None:
        return {"is_admin": False, "show_casting": False}
    is_admin = event_from_user.id in config.admin_ids
    is_fair_user = event_from_user.id in _FAIR_USER_IDS

    # Hide casting button if user already completed part 2
    already_done = False
    if is_fair_user or is_admin:
        from app.infrastructure.database.database.db import DB
        db: DB | None = dialog_manager.middleware_data.get("db")
        if db:
            app = await db.creative_applications.get_application(user_id=event_from_user.id)
            if app is not None:
                already_done = any([
                    app.part2_open_q1, app.part2_open_q2, app.part2_open_q3,
                    app.part2_case_q1, app.part2_case_q2, app.part2_case_q3,
                ])

    is_vol_part2_user = event_from_user.id in _VOL_GENERAL_PASSED_IDS

    return {
        "is_admin": is_admin,
        "show_casting": (is_admin or is_fair_user) and not already_done,
        "show_vol_part2": is_admin or is_vol_part2_user,
        "show_participant_cert": is_admin or is_cert_eligible(event_from_user.id),
    }


async def get_forum_registration_badge(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return registration badge for main menu if user is registered on forum."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    is_registered = False
    if db:
        try:
            reg = await db.forum_registrations.get_by_user_id(user_id=event_from_user.id)
            if reg and reg.get("track"):
                is_registered = True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("get_forum_registration_badge: DB error for user %d: %s", event_from_user.id, exc)
    return {
        "registration_badge": "✅ Ты успешно зарегистрирован на КБК'26!\n\n" if is_registered else "",
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
