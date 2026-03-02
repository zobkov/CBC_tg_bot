"""Database operations for creative casting applications."""

import logging

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.creative_application import (
    CreativeApplicationModel,
    CreativeApplications,
)

logger = logging.getLogger(__name__)


class _CreativeApplicationsDB:
    """Database operations for creative applications."""

    __tablename__ = "creative_applications"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_application(self, *, model: CreativeApplicationModel) -> None:
        """
        Insert or update a creative application.

        Allows user to resubmit/update their application.
        Uses user_id as the conflict key.
        """
        normalized = model.normalized_copy()
        payload = normalized.as_db_payload()

        # Remove auto-managed fields
        payload.pop("id", None)
        payload.pop("submitted_at", None)
        payload.pop("updated", None)

        stmt = insert(CreativeApplications).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[CreativeApplications.user_id],
            set_=payload,
        )
        await self.session.execute(stmt)

        logger.info(
            "Creative application saved. db='%s', user_id=%d, direction=%s",
            self.__tablename__,
            normalized.user_id,
            normalized.direction,
        )

    async def get_application(self, *, user_id: int) -> CreativeApplicationModel | None:
        """Retrieve user's application."""
        stmt = select(CreativeApplications).where(
            CreativeApplications.user_id == user_id
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()

        if entity is None:
            return None

        return entity.to_model()

    async def list_by_direction(self, *, direction: str) -> list[CreativeApplicationModel]:
        """Query all applications by direction (ceremony/fair)."""
        stmt = (
            select(CreativeApplications)
            .where(CreativeApplications.direction == direction)
            .order_by(CreativeApplications.submitted_at.desc())
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()

        return [entity.to_model() for entity in entities]

    async def list_all(self) -> list[CreativeApplicationModel]:
        """Retrieve all creative applications ordered by ID (ascending)."""
        stmt = select(CreativeApplications).order_by(CreativeApplications.id.asc())
        result = await self.session.execute(stmt)
        entities = result.scalars().all()

        return [entity.to_model() for entity in entities]

    async def update_part2_fields(
        self,
        *,
        user_id: int,
        open_q1: str | None,
        open_q2: str | None,
        open_q3: str | None,
        case_q1: str | None,
        case_q2: str | None,
        case_q3: str | None,
    ) -> None:
        """Update part 2 answer fields without touching part 1 data.

        Raises ValueError if no creative application row exists for user_id.
        """
        stmt = (
            update(CreativeApplications)
            .where(CreativeApplications.user_id == user_id)
            .values(
                part2_open_q1=open_q1,
                part2_open_q2=open_q2,
                part2_open_q3=open_q3,
                part2_case_q1=case_q1,
                part2_case_q2=case_q2,
                part2_case_q3=case_q3,
            )
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(
                f"No creative_applications row found for user_id={user_id}. "
                "Cannot save part 2 answers."
            )
        logger.info(
            "Part2 fields updated for user_id=%d (%d row(s) affected)",
            user_id,
            result.rowcount,
        )
