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

RESULTS_DATE = "\n⏰ <b>Результаты:</b> 15.10.2025, 12:00"
INTERVIEW_DEADLINE = "\n⏰ <b>Дедлайн:</b> 8.10.2025, 23:59"
DEFAULT_INTERVIEW_FEEDBACK = "Обратная связь по собеседованию пока недоступна."

UNKNOWN_STAGE_INFO: dict[str, Any] = {
    "current_stage": "Неизвестно",
    "current_stage_description": "Информация недоступна",
    "is_active": False,
    "stage_name": "Неизвестно",
    "stage_description": "",
    "stage_status": "inactive",
    "deadline_info": "",
}


def _build_stage_payload(stage_name: str, deadline: str = "") -> dict[str, Any]:
    return {
        "current_stage": "active",
        "current_stage_description": "",
        "is_active": True,
        "stage_name": stage_name,
        "stage_description": "",
        "stage_status": "active",
        "deadline_info": deadline,
    }


def _get_user(dialog_manager: DialogManager) -> User:
    return dialog_manager.event.from_user


def _get_db(dialog_manager: DialogManager) -> DB | None:
    return dialog_manager.middleware_data.get("db")


def _get_db_pool(dialog_manager: DialogManager) -> Any:
    return dialog_manager.middleware_data.get("db_applications")


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


async def _safe_user_record(db: DB, user_id: int) -> Any:
    try:
        return await db.users.get_user_record(user_id=user_id)
    except (SQLAlchemyError, AttributeError) as exc:
        LOGGER.error("Failed to read user record for %s: %s", user_id, exc)
        return None


async def _safe_evaluation(db: DB, user_id: int) -> Any:
    try:
        return await db.evaluated_applications.get_evaluation(user_id=user_id)
    except (SQLAlchemyError, AttributeError) as exc:
        LOGGER.error("Failed to fetch evaluation for %s: %s", user_id, exc)
        return None


async def _is_application_submitted(db: DB | None, user_id: int) -> bool:
    if not db:
        return False

    user_record = await _safe_user_record(db, user_id)
    return bool(user_record and user_record.submission_status == "submitted")


async def _user_passed_first_stage(db: DB | None, user_id: int) -> bool | None:
    if not db:
        return None

    evaluation = await _safe_evaluation(db, user_id)
    if evaluation is None:
        return False

    return bool(
        evaluation.accepted_1
        or evaluation.accepted_2
        or evaluation.accepted_3
    )


async def _load_feedback_data(
    db_pool: Any,
    config: Config | None,
    user_id: int,
) -> dict[str, Any] | None:
    if not db_pool or not config:
        return None

    try:
        feedback_dao = FeedbackDAO(db_pool, config)
        return await feedback_dao.get_single_user_data(user_id)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.error("Failed to fetch feedback data for %s: %s", user_id, exc)
        return None


async def _load_booking(
    db_pool: Any,
    config: Config | None,
    user_id: int,
) -> dict[str, Any] | None:
    if not db_pool or not config:
        return None

    try:
        dao = InterviewDAO(db_pool, config)
        return await dao.get_user_current_booking(user_id)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.error("Failed to fetch interview booking for %s: %s", user_id, exc)
        return None


async def _get_approved_department(
    db_pool: Any,
    config: Config | None,
    user_id: int,
) -> int | None:
    if not db_pool or not config:
        return None

    try:
        dao = InterviewDAO(db_pool, config)
        return await dao.get_user_approved_department(user_id)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.error("Failed to fetch approved department for %s: %s", user_id, exc)
        return None


async def _resolve_stage_from_feedback(
    dialog_manager: DialogManager,
    config: Config,
    user_id: int,
) -> tuple[str, str]:
    db_pool = _get_db_pool(dialog_manager)
    user_data = await _load_feedback_data(db_pool, config, user_id)

    if not user_data:
        return "Подача заявок", ""

    approved = int(user_data.get("approved") or 0)
    if approved == 0:
        return "Тестовое задание", ""

    booking = await _load_booking(db_pool, config, user_id)
    if not booking:
        return "Онлайн-собеседование", INTERVIEW_DEADLINE

    return "Онлайн-собеседование", RESULTS_DATE


async def _resolve_application_status_text(
    dialog_manager: DialogManager,
    config: Config | None,
    user_id: int,
) -> str:
    db_pool = _get_db_pool(dialog_manager)
    user_data = await _load_feedback_data(db_pool, config, user_id)

    if not user_data:
        return "Заявка подана"

    approved = int(user_data.get("approved") or 0)
    if approved == 0:
        return "Запросить обратную связь"

    booking = await _load_booking(db_pool, config, user_id)
    if not booking:
        return "Время не выбрано"

    return "Время выбрано"


def _format_booking_datetime(
    booking_date: Any,
    booking_time: Any,
) -> str | None:
    if not booking_date or not booking_time:
        return None

    try:
        if isinstance(booking_date, str):
            date_obj = datetime.strptime(booking_date, "%Y-%m-%d")
        elif isinstance(booking_date, date):
            date_obj = datetime.combine(booking_date, time.min)
        else:
            return None

        if isinstance(booking_time, str):
            time_str = booking_time
        elif isinstance(booking_time, time):
            time_str = booking_time.strftime("%H:%M")
        else:
            return None

        return f"{date_obj.strftime('%d.%m.%Y')}, {time_str}"
    except (ValueError, TypeError):
        return None


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


async def get_current_stage_info(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Describe the selection stage displayed in the guest menu."""

    config = dialog_manager.middleware_data.get("config") or _get_config(dialog_manager)
    if not config:
        return UNKNOWN_STAGE_INFO

    user = _get_user(dialog_manager)
    db = _get_db(dialog_manager)

    if not await _is_application_submitted(db, user.id):
        return _build_stage_payload("Подача заявок")

    stage_name, deadline_info = await _resolve_stage_from_feedback(
        dialog_manager,
        config,
        user.id,
    )
    return _build_stage_payload(stage_name, deadline_info)


async def get_application_status(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return application submission state and supporting text."""

    user = _get_user(dialog_manager)
    db = _get_db(dialog_manager)

    if not db:
        return {
            "application_status": "not_submitted",
            "status_text": "Заявка не подана",
            "can_apply": True,
        }

    try:
        await db.applications.create_application(user_id=user.id)
        user_record = await db.users.get_user_record(user_id=user.id)
    except (SQLAlchemyError, AttributeError) as exc:
        LOGGER.error("Failed to fetch application status for %s: %s", user.id, exc)
        return {
            "application_status": "not_submitted",
            "status_text": "Заявка не подана",
            "can_apply": True,
        }

    application_status = user_record.submission_status if user_record else "not_submitted"
    if application_status != "not_submitted":
        config = dialog_manager.middleware_data.get("config") or _get_config(dialog_manager)
        status_text = await _resolve_application_status_text(dialog_manager, config, user.id)
    else:
        status_text = "Заявка не подана"

    return {
        "application_status": application_status,
        "status_text": status_text,
        "can_apply": application_status == "not_submitted",
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


async def get_task_button_info(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Show availability info for the task submission button."""

    user = _get_user(dialog_manager)
    db = _get_db(dialog_manager)

    submission_closed = is_task_submission_closed()
    is_first_stage_passed = True
    button_emoji = "📋"

    if submission_closed:
        button_emoji = "🔒"
    else:
        first_stage_passed = await _user_passed_first_stage(db, user.id)
        if first_stage_passed is False:
            button_emoji = "🔒"
            is_first_stage_passed = False

    return {
        "task_button_emoji": button_emoji,
        "is_first_stage_passed": is_first_stage_passed,
        "submission_closed": submission_closed,
    }


async def get_task_status_info(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Summarize whether accepted tasks already have uploaded solutions."""

    user = _get_user(dialog_manager)
    db = _get_db(dialog_manager)
    default_response = {"task_status_text": "Решения не получены"}

    if not db:
        return default_response

    user_record = await _safe_user_record(db, user.id)
    evaluation = await _safe_evaluation(db, user.id)

    if not user_record or not evaluation:
        return default_response

    accepted_and_submitted = any(
        (
            evaluation.accepted_1 and user_record.task_1_submitted,
            evaluation.accepted_2 and user_record.task_2_submitted,
            evaluation.accepted_3 and user_record.task_3_submitted,
        )
    )

    if accepted_and_submitted:
        return {"task_status_text": "Решения получены"}
    return default_response


async def get_interview_button_info(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Control the interview button visibility based on approval state."""

    user = _get_user(dialog_manager)
    config = dialog_manager.middleware_data.get("config") or _get_config(dialog_manager)
    approved_department = await _get_approved_department(
        _get_db_pool(dialog_manager),
        config,
        user.id,
    )

    show_interview_button = bool(approved_department and approved_department > 0)

    return {
        "interview_button_emoji": "🔒",
        "show_interview_button": show_interview_button,
        "interview_button_enabled": False,
    }


async def get_main_menu_media(
    _dialog_manager: DialogManager,
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


async def get_feedback_button_info(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Determine whether the task feedback button should be visible."""

    db = _get_db(dialog_manager)
    user = _get_user(dialog_manager)

    if not db:
        return {"show_feedback_button": False}

    try:
        feedback_model = await db.feedback.get_user_feedback(user_id=user.id)
    except (SQLAlchemyError, AttributeError) as exc:
        LOGGER.error("Failed to fetch task feedback availability for %s: %s", user.id, exc)
        return {"show_feedback_button": False}

    show_feedback_button = bool(
        feedback_model and feedback_model.can_show_tasks_feedback()
    )
    return {"show_feedback_button": show_feedback_button}


async def get_interview_datetime_info(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Format interview datetime for the guest screen."""

    user = _get_user(dialog_manager)
    config = dialog_manager.middleware_data.get("config") or _get_config(dialog_manager)
    booking = await _load_booking(_get_db_pool(dialog_manager), config, user.id)

    if not booking:
        return {"interview_datetime": ""}

    formatted = _format_booking_datetime(
        booking.get("interview_date"),
        booking.get("start_time"),
    )

    if formatted:
        value = f"\n🕐 <b>Интервью:</b> {formatted}"
    else:
        value = (
            "\n🕐 <b>Интервью:</b> "
            f"{booking.get('interview_date')}, {booking.get('start_time')}"
        )

    return {"interview_datetime": value}


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
