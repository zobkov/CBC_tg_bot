"""Dialog data getters for the volunteer selection dialog."""

import logging
from typing import Any

from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)


async def get_main_data(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Check if user already has a volunteer application."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = dialog_manager.event
    user_id = event.from_user.id if event and event.from_user else None

    already_applied = False
    if db and user_id:
        try:
            existing = await db.volunteer_applications.get_application(user_id=user_id)
            already_applied = existing is not None
        except Exception as exc:
            logger.error(
                "[VOLUNTEER] Failed to check existing application for user %s: %s",
                user_id,
                exc,
            )

    return {"already_applied": already_applied}


async def get_confirmation_data(
    dialog_manager: DialogManager, **_kwargs: Any
) -> dict[str, Any]:
    """Fetch existing user_info fields for the confirmation window."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = dialog_manager.event
    user_id = event.from_user.id if event and event.from_user else None

    full_name = dialog_manager.dialog_data.get("vol_full_name", "")
    email = dialog_manager.dialog_data.get("vol_email", "")
    education = dialog_manager.dialog_data.get("vol_education", "")

    # If not yet in dialog_data, try to load from DB
    if db and user_id and not (full_name and email and education):
        try:
            info = await db.users_info.get_user_info(user_id=user_id)
            if info:
                full_name = full_name or info.full_name or ""
                email = email or info.email or ""
                education = education or info.education or ""
                # Cache in dialog_data for later use
                if info.full_name:
                    dialog_manager.dialog_data["vol_full_name"] = info.full_name
                if info.email:
                    dialog_manager.dialog_data["vol_email"] = info.email
                if info.education:
                    dialog_manager.dialog_data["vol_education"] = info.education
        except Exception as exc:
            logger.error(
                "[VOLUNTEER] Failed to load user_info for user %s: %s",
                user_id,
                exc,
            )

    return {
        "vol_full_name": full_name,
        "vol_email": email,
        "vol_education": education,
    }
