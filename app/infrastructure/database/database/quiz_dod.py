import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class _QuizDodDB:
    __tablename__ = "quiz_dod"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_best_result(self, *, user_id: int) -> int | None:
        result = await self.session.execute(
            text(
                """
                SELECT quiz_result
                  FROM quiz_dod
                 WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        row = result.first()
        return row.quiz_result if row else None

    async def upsert_best_result(self, *, user_id: int, quiz_result: int) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO quiz_dod (user_id, quiz_result)
                VALUES (:user_id, :quiz_result)
                ON CONFLICT (user_id) DO UPDATE
                   SET quiz_result = EXCLUDED.quiz_result
                 WHERE quiz_dod.quiz_result < EXCLUDED.quiz_result
                """
            ),
            {"user_id": user_id, "quiz_result": quiz_result},
        )
        logger.info(
            "QuizDoD result saved. db='%s', user_id=%d, quiz_result=%d",
            self.__tablename__,
            user_id,
            quiz_result,
        )
