"""Getters for the volunteer selection part 2 dialog."""

import logging
from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager

logger = logging.getLogger(__name__)


def _is_complete(record) -> bool:
    """A submission is considered complete when all three video file_ids are stored."""
    if record is None:
        return False
    return bool(record.vq1_file_id and record.vq2_file_id and record.vq3_file_id)


async def get_main_data(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Check DB: does user have a part1 application and have they already done part2?"""
    from app.infrastructure.database.database.db import DB

    db: DB | None = dialog_manager.middleware_data.get("db")
    has_part1 = False
    already_completed = False

    if db:
        try:
            part1 = await db.volunteer_applications.get_application(
                user_id=event_from_user.id
            )
            has_part1 = part1 is not None
        except Exception as exc:
            logger.error(
                "[VOL_PART2] get_main_data failed for user_id=%d: %s",
                event_from_user.id,
                exc,
            )

        try:
            part2 = await db.volunteer_selection_part2.get(user_id=event_from_user.id)
            already_completed = _is_complete(part2)
        except Exception as exc:
            logger.error(
                "[VOL_PART2] get part2 failed for user_id=%d: %s",
                event_from_user.id,
                exc,
            )

    return {
        "has_part1": has_part1,
        "already_completed": already_completed,
        "can_start": has_part1 and not already_completed,
        "no_application": not has_part1,
    }
