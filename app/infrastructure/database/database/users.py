import logging
from datetime import datetime, timezone

from psycopg import AsyncConnection, AsyncCursor

from app.infrastructure.database.models.users import UsersModel

logger = logging.getLogger(__name__)


class _UsersDB:
    __tablename__ = "users"

    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def add(
        self,
        *,
        user_id: int,
        language: str,
        is_alive: bool = True,
        is_blocked: bool = False,
    ) -> None:
        await self.connection.execute(
            """
            INSERT INTO users(user_id, language, is_alive, is_blocked)
            VALUES(%s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """,
            (user_id, language, is_alive, is_blocked),
        )
        logger.info(
            "User added. db='%s', user_id=%d, date_time='%s', "
            "language='%s', is_alive=%s, is_blocked=%s",
            self.__tablename__,
            user_id,
            datetime.now(timezone.utc),
            language,
            is_alive,
            is_blocked,
        )

    async def delete(self, *, user_id: int) -> None:
        await self.connection.execute(
            """
            DELETE FROM users WHERE user_id = %s;
        """,
            (user_id,),
        )
        logger.info("User deleted. db='%s', user_id='%d'", self.__tablename__, user_id)

    async def get_user_record(self, *, user_id: int) -> UsersModel | None:
        cursor: AsyncCursor = await self.connection.execute(
            """
         SELECT user_id,
             created,
             language,
             is_alive,
             is_blocked,
             submission_status,
             task_1_submitted,
             task_2_submitted,
             task_3_submitted
            FROM users
            WHERE users.user_id = %s
        """,
            (user_id,),
        )
        data = await cursor.fetchone()
        return UsersModel(*data) if data else None

    async def update_alive_status(self, *, user_id: int, is_alive: bool = True) -> None:
        await self.connection.execute(
            """
            UPDATE users
            SET is_alive = %s
            WHERE user_id = %s
        """,
            (is_alive, user_id),
        )
        logger.info(
            "User updated. db='%s', user_id=%d, is_alive=%s",
            self.__tablename__,
            user_id,
            is_alive,
        )

    async def update_user_lang(self, *, user_id: int, user_lang: str) -> None:
        await self.connection.execute(
            """
            UPDATE users
            SET language = %s
            WHERE user_id = %s
        """,
            (user_lang, user_id),
        )
        logger.info(
            "User updated. db='%s', user_id=%d, language=%s",
            self.__tablename__,
            user_id,
            user_lang,
        )

    async def set_submission_status(self, *, user_id: int, status: str) -> None:
        await self.connection.execute(
            """
            UPDATE users
            SET submission_status = %s
            WHERE user_id = %s
        """,
            (status, user_id),
        )
        logger.info(
            "User updated. db='%s', user_id=%d, submission_status=%s",
            self.__tablename__,
            user_id,
            status,
        )

    async def list_user_ids_by_group(self, *, group: str) -> list[int]:
        if group in ("not_submitted", "submitted"):
            # Старая логика на основе submission_status
            cursor: AsyncCursor = await self.connection.execute(
                """
                SELECT user_id FROM users WHERE submission_status = %s AND is_blocked = FALSE
            """,
                (group,),
            )
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
        
        elif group == "accepted":
            # Пользователи, принятые хотя бы по одному заданию (любая из трех колонок = true)
            cursor: AsyncCursor = await self.connection.execute(
                """
                SELECT u.user_id FROM users u
                INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
                WHERE u.is_blocked = FALSE 
                AND (ea.accepted_1 = TRUE OR ea.accepted_2 = TRUE OR ea.accepted_3 = TRUE)
            """,
            )
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
        
        elif group == "not_accepted":
            # Пользователи, НЕ принятые ни по одному заданию (все три колонки = false)
            cursor: AsyncCursor = await self.connection.execute(
                """
                SELECT u.user_id FROM users u
                INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
                WHERE u.is_blocked = FALSE 
                AND ea.accepted_1 = FALSE AND ea.accepted_2 = FALSE AND ea.accepted_3 = FALSE
            """,
            )
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
        
        else:
            logger.warning("Unknown group '%s', returning empty list", group)
            return []

    async def set_task_submission_status(self, *, user_id: int, task_number: int, submitted: bool = True) -> None:
        """Устанавливает статус отправки конкретного задания"""
        column_name = f"task_{task_number}_submitted"
        await self.connection.execute(
            f"""
            UPDATE users
            SET {column_name} = %s
            WHERE user_id = %s
        """,
            (submitted, user_id),
        )
        logger.info(
            "User task submission updated. db='%s', user_id=%d, task=%d, submitted=%s",
            self.__tablename__,
            user_id,
            task_number,
            submitted,
        )

    async def get_task_submission_status(self, *, user_id: int, task_number: int) -> bool:
        """Получает статус отправки конкретного задания"""
        column_name = f"task_{task_number}_submitted"
        cursor: AsyncCursor = await self.connection.execute(
            f"""
            SELECT {column_name}
            FROM users
            WHERE user_id = %s
        """,
            (user_id,),
        )
        result = await cursor.fetchone()
        return result[0] if result else False
