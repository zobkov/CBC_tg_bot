"""Dialog data getters for the volunteer selection dialog."""

import logging
from typing import Any

from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)

_ROLE_LABELS = {
    "general": "Общий волонтёрский функционал",
    "photo": "Фотографирование",
    "translate": "Перевод",
}


def _parse_roles(function_str: str | None) -> set[str]:
    """Parse comma-separated function string into a set of role keys."""
    if not function_str:
        return set()
    return {r.strip() for r in function_str.split(",") if r.strip()}


async def get_main_data(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Check if user already has a volunteer application."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = dialog_manager.event
    user_id = event.from_user.id if event and event.from_user else None

    already_applied = False
    applied_roles: set[str] = set()
    if db and user_id:
        try:
            existing = await db.volunteer_applications.get_application(user_id=user_id)
            if existing is not None:
                already_applied = True
                applied_roles = _parse_roles(existing.function)
        except Exception as exc:
            logger.error(
                "[VOLUNTEER] Failed to check existing application for user %s: %s",
                user_id,
                exc,
            )

    return {"already_applied": already_applied, "applied_roles": applied_roles, "not_already_applied": not already_applied}


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


async def get_another_role_data(
    dialog_manager: DialogManager, **_kwargs: Any
) -> dict[str, Any]:
    """Data for the another_role window: which roles are already filled."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = dialog_manager.event
    user_id = event.from_user.id if event and event.from_user else None

    filled_roles: set[str] = set()
    if db and user_id:
        try:
            existing = await db.volunteer_applications.get_application(user_id=user_id)
            if existing:
                filled_roles = _parse_roles(existing.function)
                # Cache phone/dates into dialog_data so the re-application flow
                # can skip those steps.
                if existing.phone and not dialog_manager.dialog_data.get("vol_phone"):
                    dialog_manager.dialog_data["vol_phone"] = existing.phone
                if existing.volunteer_dates and not dialog_manager.dialog_data.get("vol_volunteer_dates"):
                    dialog_manager.dialog_data["vol_volunteer_dates"] = existing.volunteer_dates
        except Exception as exc:
            logger.error(
                "[VOLUNTEER] get_another_role_data failed for user %s: %s",
                user_id,
                exc,
            )

    def _role_label(key: str) -> str:
        label = _ROLE_LABELS.get(key, key)
        prefix = "✅ " if key in filled_roles else "➕ "
        return prefix + label

    return {
        "general_btn_label": _role_label("general"),
        "photo_btn_label": _role_label("photo"),
        "translate_btn_label": _role_label("translate"),
        "filled_roles": filled_roles,
    }


async def get_overwrite_confirm_data(
    dialog_manager: DialogManager, **_kwargs: Any
) -> dict[str, Any]:
    """Data for the overwrite_confirm window."""
    role_key = dialog_manager.dialog_data.get("overwriting_role", "")
    label = _ROLE_LABELS.get(role_key, role_key)
    return {"overwriting_role_label": label}
