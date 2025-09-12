from datetime import datetime
from typing import Dict, Any

from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType

from config.config import Config
from app.infrastructure.database.database.db import DB
from app.utils.optimized_dialog_widgets import get_file_id_for_path


async def get_live_tasks_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о пользователе"""
    
    return {
        "task_1_is_live" : True,
        "task_2_is_live" : False,
        "task_3_is_live" : True
    }

async def get_user_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о пользователе"""
    
    return {
        "user_id": event_from_user.id,
        "username": event_from_user.username or "",
        "first_name": event_from_user.first_name or "",
        "last_name": event_from_user.last_name or "",
    }
