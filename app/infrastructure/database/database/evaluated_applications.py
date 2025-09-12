import logging
from datetime import datetime, timezone

from psycopg import AsyncConnection, AsyncCursor

from app.infrastructure.database.models.evaluated_applications import EvaluatedApplicationModel

logger = logging.getLogger(__name__)


class _EvaluatedApplicationsDB:
    __tablename__ = "evaluated_applications"

    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def get_evaluation(self, *, user_id: int) -> EvaluatedApplicationModel | None:
        """Получить данные оценки пользователя по его ID"""
        cursor: AsyncCursor = await self.connection.execute(
            """
            SELECT id, user_id, accepted_1, accepted_2, accepted_3, created, updated
            FROM evaluated_applications
            WHERE user_id = %s
        """,
            (user_id,),
        )
        data = await cursor.fetchone()
        return EvaluatedApplicationModel(*data) if data else None

    async def create_evaluation(
        self,
        *,
        user_id: int,
        accepted_1: bool = False,
        accepted_2: bool = False,
        accepted_3: bool = False,
    ) -> None:
        """Создать новую запись оценки для пользователя"""
        await self.connection.execute(
            """
            INSERT INTO evaluated_applications(user_id, accepted_1, accepted_2, accepted_3, created, updated)
            VALUES(%s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING;
        """,
            (user_id, accepted_1, accepted_2, accepted_3, datetime.now(timezone.utc), datetime.now(timezone.utc)),
        )
        logger.info(
            "Evaluation created. db='%s', user_id=%d, accepted_1=%s, accepted_2=%s, accepted_3=%s",
            self.__tablename__,
            user_id,
            accepted_1,
            accepted_2,
            accepted_3,
        )

    async def update_evaluation(
        self,
        *,
        user_id: int,
        accepted_1: bool | None = None,
        accepted_2: bool | None = None,
        accepted_3: bool | None = None,
    ) -> None:
        """Обновить данные оценки пользователя"""
        # Строим динамический запрос только для переданных параметров
        set_clauses = []
        params = []
        
        if accepted_1 is not None:
            set_clauses.append("accepted_1 = %s")
            params.append(accepted_1)
        if accepted_2 is not None:
            set_clauses.append("accepted_2 = %s")
            params.append(accepted_2)
        if accepted_3 is not None:
            set_clauses.append("accepted_3 = %s")
            params.append(accepted_3)
        
        if not set_clauses:
            logger.warning("No fields to update for user_id=%d", user_id)
            return
        
        set_clauses.append("updated = %s")
        params.append(datetime.now(timezone.utc))
        params.append(user_id)
        
        query = f"""
            UPDATE evaluated_applications
            SET {', '.join(set_clauses)}
            WHERE user_id = %s
        """
        
        await self.connection.execute(query, params)
        logger.info(
            "Evaluation updated. db='%s', user_id=%d",
            self.__tablename__,
            user_id,
        )

    async def delete_evaluation(self, *, user_id: int) -> None:
        """Удалить данные оценки пользователя"""
        await self.connection.execute(
            """
            DELETE FROM evaluated_applications WHERE user_id = %s;
        """,
            (user_id,),
        )
        logger.info("Evaluation deleted. db='%s', user_id='%d'", self.__tablename__, user_id)

    async def get_accepted_count_by_task(self) -> dict[str, int]:
        """Получить количество принятых по каждому заданию"""
        cursor: AsyncCursor = await self.connection.execute(
            """
            SELECT 
                SUM(CASE WHEN accepted_1 = true THEN 1 ELSE 0 END) as accepted_1_count,
                SUM(CASE WHEN accepted_2 = true THEN 1 ELSE 0 END) as accepted_2_count,
                SUM(CASE WHEN accepted_3 = true THEN 1 ELSE 0 END) as accepted_3_count
            FROM evaluated_applications
        """
        )
        data = await cursor.fetchone()
        return {
            "accepted_1_count": data[0] or 0,
            "accepted_2_count": data[1] or 0,
            "accepted_3_count": data[2] or 0,
        } if data else {"accepted_1_count": 0, "accepted_2_count": 0, "accepted_3_count": 0}

    async def list_users_by_acceptance(self, *, task_number: int) -> list[int]:
        """Получить список пользователей, принятых по определенному заданию"""
        if task_number not in [1, 2, 3]:
            raise ValueError("task_number должен быть 1, 2 или 3")
        
        cursor: AsyncCursor = await self.connection.execute(
            f"""
            SELECT user_id FROM evaluated_applications 
            WHERE accepted_{task_number} = true
        """
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]