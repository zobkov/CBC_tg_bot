"""Getters for the creative selection part 2 dialog."""

from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager


def _is_part2_done(app) -> bool:
    """Return True if the application has at least one part2 field filled."""
    if app is None:
        return False
    return any([
        app.part2_open_q1, app.part2_open_q2, app.part2_open_q3,
        app.part2_case_q1, app.part2_case_q2, app.part2_case_q3,
    ])


async def get_part2_main_data(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Check DB to determine whether the user has already completed part 2."""
    from app.infrastructure.database.database.db import DB
    import logging
    _logger = logging.getLogger(__name__)

    db: DB | None = dialog_manager.middleware_data.get("db")
    already_completed = False
    has_application = False
    if db:
        app = await db.creative_applications.get_application(user_id=event_from_user.id)
        has_application = app is not None
        already_completed = _is_part2_done(app)
        if not has_application:
            _logger.warning(
                "[PART2] No creative application found for user_id=%d",
                event_from_user.id,
            )
    else:
        _logger.error("[PART2] db not available in middleware_data for user_id=%d", event_from_user.id)

    return {
        "already_completed": already_completed,
        "can_start": has_application and not already_completed,
        "no_application": not has_application,
    }


_CONFIRM_PER_ANSWER_LIMIT = 600
_TRUNCATION_SUFFIX = "… [сокращено для отображения здесь]"


def _trunc(text: str) -> str:
    """Truncate answer text for the confirmation preview if it is too long."""
    if len(text) <= _CONFIRM_PER_ANSWER_LIMIT:
        return text
    return text[: _CONFIRM_PER_ANSWER_LIMIT - len(_TRUNCATION_SUFFIX)] + _TRUNCATION_SUFFIX


async def get_part2_confirmation_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return answers from dialog_data for the confirmation summary window."""
    dd = dialog_manager.dialog_data
    return {
        "q1": _trunc(dd.get("part2_q1", "—")),
        "q2": _trunc(dd.get("part2_q2", "—")),
        "q3": _trunc(dd.get("part2_q3", "—")),
        "q4": _trunc(dd.get("part2_q4", "—")),
        "q5": _trunc(dd.get("part2_q5", "—")),
        "q6": _trunc(dd.get("part2_q6", "—")),
    }
