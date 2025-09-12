from datetime import datetime
from typing import Dict, Any
import logging

from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType

from config.config import Config
from app.infrastructure.database.database.db import DB
from app.utils.optimized_dialog_widgets import get_file_id_for_path

logger = logging.getLogger(__name__)


async def get_live_tasks_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о принятии пользователя по заданиям"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        # Если БД недоступна, возвращаем дефолтные значения
        return {
            "task_1_is_live": False,
            "task_2_is_live": False,
            "task_3_is_live": False
        }
    
    try:
        # Получаем данные оценки пользователя из БД
        evaluation = await db.evaluated_applications.get_evaluation(user_id=event_from_user.id)
        
        if evaluation:
            return {
                "task_1_is_live": evaluation.accepted_1,
                "task_2_is_live": evaluation.accepted_2,
                "task_3_is_live": evaluation.accepted_3
            }
        else:
            # Если данных нет, возвращаем False для всех заданий
            return {
                "task_1_is_live": False,
                "task_2_is_live": False,
                "task_3_is_live": False
            }
    except Exception as e:
        # В случае ошибки логируем и возвращаем дефолтные значения
        logger.error(f"Error getting evaluation for user {event_from_user.id}: {e}")
        return {
            "task_1_is_live": False,
            "task_2_is_live": False,
            "task_3_is_live": False
        }

async def get_user_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о пользователе"""
    
    return {
        "user_id": event_from_user.id,
        "username": event_from_user.username or "",
        "first_name": event_from_user.first_name or "",
        "last_name": event_from_user.last_name or "",
    }
