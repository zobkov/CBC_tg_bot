"""Database operations for volunteer selection part 2."""

import logging

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.volunteer_selection_part2 import (
    VolSelPart2Model,
    VolSelPart2,
)

logger = logging.getLogger(__name__)


class _VolSelPart2DB:
    """Database operations for volunteer_selection_part2 table."""

    __tablename__ = "volunteer_selection_part2"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, *, model: VolSelPart2Model) -> None:
        """Insert or update a part 2 submission (keyed by user_id)."""
        payload = model.as_db_payload()
        payload.pop("id", None)
        payload.pop("submitted_at", None)
        payload.pop("updated", None)

        stmt = insert(VolSelPart2).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[VolSelPart2.user_id],
            set_=payload,
        )
        await self.session.execute(stmt)

        logger.info(
            "[VOL_PART2] Saved part2 for user_id=%d",
            model.user_id,
        )

    async def get(self, *, user_id: int) -> VolSelPart2Model | None:
        """Retrieve an existing part 2 submission for a user, or None."""
        stmt = select(VolSelPart2).where(VolSelPart2.user_id == user_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()

    async def count_all(self) -> int:
        """Return total number of part2 submissions."""
        stmt = select(func.count()).select_from(VolSelPart2)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_page(self, *, page: int, limit: int = 10) -> list[VolSelPart2]:
        """Return ORM entities for a given page (0-indexed), ordered by id."""
        stmt = (
            select(VolSelPart2)
            .order_by(VolSelPart2.id.asc())
            .offset(page * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list["VolSelPart2Model"]:
        """Return all part2 submissions as models, ordered by id."""
        stmt = select(VolSelPart2).order_by(VolSelPart2.id.asc())
        result = await self.session.execute(stmt)
        return [entity.to_model() for entity in result.scalars().all()]

    async def set_reviewed(self, *, user_id: int, reviewed: bool) -> None:
        """Set the reviewed flag for a single part2 submission."""
        from sqlalchemy import update

        stmt = (
            update(VolSelPart2)
            .where(VolSelPart2.user_id == user_id)
            .values(reviewed=reviewed)
        )
        await self.session.execute(stmt)
