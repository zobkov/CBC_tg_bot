"""Main staff dialogs getters"""
from typing import Dict, Any, Optional
import logging

from aiogram.enums import ContentType
from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from config.config import Config, load_config
from app.infrastructure.database.database.db import DB
from app.utils.optimized_dialog_widgets import get_file_id_for_path


logger = logging.getLogger(__name__)


def _get_config(dialog_manager: DialogManager) -> Config:
    config: Optional[Config] = dialog_manager.middleware_data.get("config")
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

    logger.warning("Getter could not get the instance of the config. Loading config from .env. " \
    "This is an unexpected behaviour. Please check the root cause.")
    return load_config()


async def get_user_info(
        event_from_user: User,
        **_kwargs
        ) -> Dict[str, Any]: # pylint: disable=unused-argument
    """Get telegram user information"""
    return {
        "user_id": event_from_user.id,
        "username": event_from_user.username or "",
        "first_name": event_from_user.first_name or "",
        "last_name": event_from_user.last_name or "",
    }

async def get_db_user_info(
        dialog_manager: DialogManager,
        event_from_user: User,
        **_kwargs
        ) -> Dict[str, Any]:
    """Get all information about user from database"""
    db: DB = None
    NotImplemented # TODO add this getter after user_info DB migration


async def get_support_contacts(dialog_manager: DialogManager, **_kwargs) -> Dict[str, Any]:
    """Supports contacts getter"""
    config: Config = dialog_manager.middleware_data.get("config")

    if not config:
        return {
            "general_support": "Недоступно",
            "technical_support": "Недоступно",
            "hr_support": "Недоступно"
        }

    return {
        "general_support": config.selection.support_contacts["general"],
        "technical_support": config.selection.support_contacts["technical"],
        "hr_support": config.selection.support_contacts["hr"]
    }


async def get_main_menu_media(**_kwargs) -> Dict[str, Any]:
    """Получаем медиа для главного меню"""
    file_id = get_file_id_for_path("main_menu/main_menu.jpg")

    if file_id:
        # Используем file_id для быстрой отправки
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        # Fallback на путь к файлу
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path="app/bot/assets/images/main_menu/main_menu.jpg"
        )

    return {
        "media": media
    }
