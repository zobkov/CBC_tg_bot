import logging
from datetime import datetime, timezone
from typing import Optional

from psycopg import AsyncConnection, AsyncCursor

from app.infrastructure.database.models.task_statistics import TaskStatisticsModel

logger = logging.getLogger(__name__)


class _TaskStatisticsDB:
    __tablename__ = "task_statistics"

    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def record_user_access(
        self,
        *,
        user_id: int,
        username: Optional[str] = None,
    ) -> bool:
        """
        Записывает пользователя в статистику при первом заходе в TaskSG.main.
        Возвращает True если запись была добавлена, False если пользователь уже был записан.
        """
        try:
            async with self.connection.cursor() as cursor:
                # Проверяем, есть ли уже запись для данного пользователя
                await cursor.execute(
                    "SELECT id FROM task_statistics WHERE user_id = %s",
                    (user_id,)
                )
                existing_record = await cursor.fetchone()
                
                if existing_record:
                    logger.debug(f"User {user_id} already exists in task_statistics")
                    return False
                
                # Добавляем новую запись
                await cursor.execute(
                    """
                    INSERT INTO task_statistics(user_id, username, date_first_accessed)
                    VALUES(%s, %s, %s)
                    """,
                    (user_id, username, datetime.now(timezone.utc)),
                )
                
                logger.info(
                    "Task statistics recorded. db='%s', user_id=%d, username='%s', date_time='%s'",
                    self.__tablename__,
                    user_id,
                    username or "None",
                    datetime.now(timezone.utc),
                )
                return True
                
        except Exception as e:
            logger.error(f"Error recording task statistics for user {user_id}: {e}")
            return False

    async def get_statistics_record(self, *, user_id: int) -> Optional[TaskStatisticsModel]:
        """Получает запись статистики для указанного пользователя."""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, user_id, username, date_first_accessed
                    FROM task_statistics
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                record = await cursor.fetchone()
                
                if record:
                    return TaskStatisticsModel(
                        id=record[0],
                        user_id=record[1],
                        username=record[2],
                        date_first_accessed=record[3]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting task statistics for user {user_id}: {e}")
            return None

    async def get_total_users_count(self) -> int:
        """Возвращает общее количество пользователей, которые заходили в TaskSG.main."""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM task_statistics")
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting total users count from task statistics: {e}")
            return 0