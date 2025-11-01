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
        education: str,
    ) -> None:
        await self.connection.execute(
            """
            INSERT INTO quiz_dod_users_info (user_id, full_name, phone, email, education)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                phone = EXCLUDED.phone,
                email = EXCLUDED.email,
                education = EXCLUDED.education
            """,
            (user_id, full_name, phone, email, education),
        )
        logger.info(
            "QuizDoD user info saved. db='%s', user_id=%d",
            self.__tablename__,
            user_id,
        )

    async def mark_certificate_requested(self, user_id: int) -> None:
        cursor = await self.connection.execute(
            """
            UPDATE quiz_dod_users_info
            SET requested_certificate = TRUE
            WHERE user_id = %s
            """,
            (user_id,),
        )

        if cursor.rowcount == 0:
            logger.warning(
                "QuizDoD certificate flag not updated: user_id=%d not found",
                user_id,
            )
        else:
            logger.info(
                "QuizDoD certificate requested marked. db='%s', user_id=%d",
                self.__tablename__,
                user_id,
            )

    async def get_certificate_status(self, user_id: int) -> bool | None:
        cursor = await self.connection.execute(
            """
            SELECT requested_certificate
            FROM quiz_dod_users_info
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        requested_certificate = row[0]
        return bool(requested_certificate)
