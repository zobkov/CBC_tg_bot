import logging

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)


class _QuizDodUsersInfoDB:
    __tablename__ = "quiz_dod_users_info"

    def __init__(self, connection: AsyncConnection) -> None:
        self.connection = connection

    async def upsert_user_info(
        self,
        *,
        user_id: int,
        full_name: str,
        phone: str,
        email: str,
    ) -> None:
        await self.connection.execute(
            """
            INSERT INTO quiz_dod_users_info (user_id, full_name, phone, email)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                phone = EXCLUDED.phone,
                email = EXCLUDED.email
            """,
            (user_id, full_name, phone, email),
        )
        logger.info(
            "QuizDoD user info saved. db='%s', user_id=%d",
            self.__tablename__,
            user_id,
        )
