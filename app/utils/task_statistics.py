"""
Утилиты для работы со статистикой пользователей в TaskSG.main
"""
import logging
from typing import Optional

from aiogram.types import User
from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)


async def record_task_statistics(db: DB, user: User) -> bool:
    """
    Записывает статистику пользователя при заходе в TaskSG.main.
    Каждый пользователь записывается только один раз.
    
    Args:
        db: Экземпляр базы данных
        user: Пользователь Telegram
    
    Returns:
        bool: True если запись была добавлена, False если пользователь уже был записан
    """
    if not db:
        logger.warning("Database connection not available for task statistics")
        return False
    
    try:
        username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip()
        
        success = await db.task_statistics.record_user_access(
            user_id=user.id,
            username=username if username else None
        )
        
        if success:
            logger.info(f"Task statistics recorded for user {user.id} ({username})")
        else:
            logger.debug(f"User {user.id} already exists in task statistics")
            
        return success
        
    except Exception as e:
        logger.error(f"Error recording task statistics for user {user.id}: {e}")
        return False


async def get_task_statistics_count(db: DB) -> int:
    """
    Возвращает общее количество уникальных пользователей, которые заходили в TaskSG.main.
    
    Args:
        db: Экземпляр базы данных
    
    Returns:
        int: Количество уникальных пользователей
    """
    if not db:
        logger.warning("Database connection not available for task statistics")
        return 0
    
    try:
        count = await db.task_statistics.get_total_users_count()
        return count
    except Exception as e:
        logger.error(f"Error getting task statistics count: {e}")
        return 0