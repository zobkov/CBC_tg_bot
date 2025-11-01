import logging

from psycopg import AsyncConnection, AsyncCursor

logger = logging.getLogger(__name__)


class _QuizDodDB:
    __tablename__ = "quiz_dod"

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def get_best_result(self, *, user_id: int) -> int | None:
        cursor: AsyncCursor = await self.connection.execute(
            """
            SELECT quiz_result
            FROM quiz_dod
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def upsert_best_result(self, *, user_id: int, quiz_result: int) -> None:
        await self.connection.execute(
            """
            INSERT INTO quiz_dod (user_id, quiz_result)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET quiz_result = EXCLUDED.quiz_result
            WHERE quiz_dod.quiz_result < EXCLUDED.quiz_result
            """,
            (user_id, quiz_result),
        )
        logger.info(
            "QuizDoD result saved. db='%s', user_id=%d, quiz_result=%d",
            self.__tablename__,
            user_id,
            quiz_result,
        )
