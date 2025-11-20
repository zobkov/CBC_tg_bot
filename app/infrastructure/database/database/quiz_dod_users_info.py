import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class _QuizDodUsersInfoDB:
    __tablename__ = "quiz_dod_users_info"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_user_info(
        self,
        *,
        user_id: int,
        full_name: str,
        phone: str,
        email: str,
        education: str,
    ) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO quiz_dod_users_info (user_id, full_name, phone, email, education)
                VALUES (:user_id, :full_name, :phone, :email, :education)
                ON CONFLICT (user_id) DO UPDATE
                   SET full_name = EXCLUDED.full_name,
                       phone = EXCLUDED.phone,
                       email = EXCLUDED.email,
                       education = EXCLUDED.education
                """
            ),
            {
                "user_id": user_id,
                "full_name": full_name,
                "phone": phone,
                "email": email,
                "education": education,
            },
        )
        logger.info(
            "QuizDoD user info saved. db='%s', user_id=%d",
            self.__tablename__,
            user_id,
        )

    async def mark_certificate_requested(self, user_id: int) -> None:
        result = await self.session.execute(
            text(
                """
                UPDATE quiz_dod_users_info
                   SET requested_certificate = TRUE
                 WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        )

        if result.rowcount == 0:
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
        result = await self.session.execute(
            text(
                """
                SELECT requested_certificate
                  FROM quiz_dod_users_info
                 WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        row = result.first()
        if not row:
            return None
        return bool(row.requested_certificate)
