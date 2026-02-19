"""Data getters for settings dialog."""

from __future__ import annotations

import logging
from typing import Any

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from aiogram.enums import ContentType

from app.infrastructure.database.database.db import DB
from config.config import Config

from app.utils.optimized_dialog_widgets import get_file_id_for_path

logger = logging.getLogger(__name__)


async def get_user_profile(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Get user profile data for display."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    user = dialog_manager.event.from_user
    
    if not db or not user:
        return {
            "full_name": "Не указано",
            "education": "Не указано",
            "email": "Не указано",
        }
    
    try:
        user_info = await db.users_info.get_user_info(user_id=user.id)
        
        if user_info:
            return {
                "full_name": user_info.full_name or "Не указано",
                "education": user_info.education or "Не указано",
                "email": user_info.email or "Не указано",
            }
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
    
    return {
        "full_name": "Не указано",
        "education": "Не указано",
        "email": "Не указано",
    }


async def get_support_contacts(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Expose support contacts configured in settings."""
    config: Config | None = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {
            "general_support": "Недоступно",
            "technical_support": "Недоступно",
        }
    
    contacts = config.selection.support_contacts
    return {
        "general_support": contacts["general"],
        "technical_support": contacts["technical"],
    }

async def get_support_media(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Load photo attachment definition for the guest main menu."""

    file_id = get_file_id_for_path("support/support.png")
    if file_id:
        media = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path="app/bot/assets/images/support/support.png",
        )

    return {"media": media}
