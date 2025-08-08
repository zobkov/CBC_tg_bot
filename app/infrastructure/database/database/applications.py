import logging
from datetime import datetime, timezone
from typing import Optional

from psycopg import AsyncConnection, AsyncCursor

from app.bot.enums.application_status import ApplicationStatus
from app.infrastructure.database.models.applications import ApplicationsModel

logger = logging.getLogger(__name__)


class _ApplicationsDB:
    __tablename__ = "applications"

    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create_application(
        self,
        *,
        user_id: int,
        status: ApplicationStatus = ApplicationStatus.NOT_SUBMITTED,
    ) -> None:
        await self.connection.execute(
            """
            INSERT INTO applications(user_id, status, created, updated)
            VALUES(%s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING;
        """,
            (user_id, status.value, datetime.now(timezone.utc), datetime.now(timezone.utc)),
        )
        logger.info(
            "Application created. db='%s', user_id=%d, status=%s",
            self.__tablename__,
            user_id,
            status.value,
        )

    async def get_application(self, *, user_id: int) -> ApplicationsModel | None:
        cursor: AsyncCursor = await self.connection.execute(
            """
            SELECT id, user_id, status, created, updated,
                   full_name, university, course, phone, email, telegram_username,
                   how_found_kbk, department, position, experience, motivation,
                   resume_local_path, resume_google_drive_url
            FROM applications
            WHERE user_id = %s
        """,
            (user_id,),
        )
        data = await cursor.fetchone()
        return ApplicationsModel(*data) if data else None

    async def update_application_status(
        self, *, user_id: int, status: ApplicationStatus
    ) -> None:
        await self.connection.execute(
            """
            UPDATE applications
            SET status = %s, updated = %s
            WHERE user_id = %s
        """,
            (status.value, datetime.now(timezone.utc), user_id),
        )
        logger.info(
            "Application status updated. db='%s', user_id=%d, status=%s",
            self.__tablename__,
            user_id,
            status.value,
        )

    async def update_first_stage_form(
        self,
        *,
        user_id: int,
        full_name: str,
        university: str,
        course: int,
        phone: str,
        email: str,
        telegram_username: str,
        how_found_kbk: str,
        department: str,
        position: str,
        experience: str,
        motivation: str,
        resume_local_path: Optional[str] = None,
        resume_google_drive_url: Optional[str] = None,
    ) -> None:
        await self.connection.execute(
            """
            UPDATE applications
            SET full_name = %s, university = %s, course = %s, phone = %s, email = %s,
                telegram_username = %s, how_found_kbk = %s, department = %s, position = %s,
                experience = %s, motivation = %s, resume_local_path = %s, 
                resume_google_drive_url = %s, updated = %s
            WHERE user_id = %s
        """,
            (
                full_name, university, course, phone, email, telegram_username,
                how_found_kbk, department, position, experience, motivation,
                resume_local_path, resume_google_drive_url, 
                datetime.now(timezone.utc), user_id
            ),
        )
        logger.info(
            "Application first stage form updated. db='%s', user_id=%d",
            self.__tablename__,
            user_id,
        )
