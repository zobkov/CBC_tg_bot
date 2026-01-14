import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.broadcasts import BroadcastModel, Broadcasts

logger = logging.getLogger(__name__)


class _BroadcastsDB:
    __tablename__ = "broadcasts"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        *,
        key: str,
        title: str | None = None,
        description: str | None = None,
        channel: str | None = None,
        enabled: bool = True,
    ) -> None:
        stmt = (
            insert(Broadcasts)
            .values(
                key=key,
                title=title,
                description=description,
                channel=channel,
                enabled=enabled,
            )
            .on_conflict_do_nothing(index_elements=[Broadcasts.key])
        )
        await self.session.execute(stmt)
        logger.info(
            "Broadcast added. db='%s', key=%s, title=%s",
            self.__tablename__,
            key,
            title,
        )

    async def delete(self, *, key: str) -> None:
        stmt = delete(Broadcasts).where(Broadcasts.key == key)
        await self.session.execute(stmt)
        logger.info("Broadcast deleted. db='%s', key=%s", self.__tablename__, key)

    async def get_by_key(self, *, key: str) -> BroadcastModel | None:
        stmt = select(Broadcasts).where(Broadcasts.key == key)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()

    async def list_all(self) -> list[BroadcastModel]:
        result = await self.session.execute(select(Broadcasts))
        rows = result.scalars().all()
        return [r.to_model() for r in rows]

    async def set_enabled(self, *, key: str, enabled: bool) -> None:
        stmt = update(Broadcasts).where(Broadcasts.key == key).values(enabled=enabled)
        await self.session.execute(stmt)
        logger.info("Broadcast enabled=%s. key=%s", enabled, key)
