"""Database operations for volunteer applications."""

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.volunteer_application import (
    VolunteerApplicationModel,
    VolunteerApplications,
)

logger = logging.getLogger(__name__)


class _VolunteerApplicationsDB:
    """Database operations for volunteer applications."""

    __tablename__ = "volunteer_applications"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_application(self, *, model: VolunteerApplicationModel) -> None:
        """
        Insert or update a volunteer application.

        Uses user_id as the conflict key so users can re-submit.
        """
        normalized = model.normalized_copy()
        payload = normalized.as_db_payload()

        payload.pop("id", None)
        payload.pop("submitted_at", None)
        payload.pop("updated", None)

        stmt = insert(VolunteerApplications).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[VolunteerApplications.user_id],
            set_=payload,
        )
        await self.session.execute(stmt)

        logger.info(
            "Volunteer application saved. db='%s', user_id=%d, function=%s",
            self.__tablename__,
            normalized.user_id,
            normalized.function,
        )

    async def get_application(self, *, user_id: int) -> VolunteerApplicationModel | None:
        """Retrieve a user's volunteer application."""
        stmt = select(VolunteerApplications).where(
            VolunteerApplications.user_id == user_id
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()

        if entity is None:
            return None

        return entity.to_model()

    async def list_all(self) -> list[VolunteerApplicationModel]:
        """Retrieve all volunteer applications ordered by ID (ascending)."""
        stmt = select(VolunteerApplications).order_by(VolunteerApplications.id.asc())
        result = await self.session.execute(stmt)
        entities = result.scalars().all()

        return [entity.to_model() for entity in entities]
