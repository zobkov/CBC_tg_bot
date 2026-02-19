import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.online_events import OnlineEventModel, OnlineEvents

logger = logging.getLogger(__name__)


class _OnlineEventsDB:
    __tablename__ = "online_events"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_from_config(
        self,
        *,
        slug: str,
        alias: str,
        title: str,
        speaker: str | None = None,
        description: str | None = None,
        url: str | None = None,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        """Insert or update event from config file."""
        stmt = (
            insert(OnlineEvents)
            .values(
                slug=slug,
                alias=alias,
                title=title,
                speaker=speaker,
                description=description,
                url=url,
                start_at=start_at,
                end_at=end_at,
            )
            .on_conflict_do_update(
                index_elements=[OnlineEvents.slug],
                set_={
                    "alias": alias,
                    "title": title,
                    "speaker": speaker,
                    "description": description,
                    "url": url,
                    "start_at": start_at,
                    "end_at": end_at,
                },
            )
        )
        await self.session.execute(stmt)
        logger.info(
            "Online event upserted. db='%s', slug=%s, title=%s",
            self.__tablename__,
            slug,
            title,
        )

    async def get_by_slug(self, *, slug: str) -> OnlineEventModel | None:
        """Get event by slug identifier."""
        stmt = select(OnlineEvents).where(OnlineEvents.slug == slug)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()

    async def get_by_id(self, *, id: int) -> OnlineEventModel | None:
        """Get event by database ID."""
        stmt = select(OnlineEvents).where(OnlineEvents.id == id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()

    async def list_active_upcoming(self, *, hide_older_than_hours: int = 3) -> list[OnlineEventModel]:
        """List active events, hiding those that started more than N hours ago."""
        # Calculate cutoff time in Python
        from datetime import datetime, timezone, timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hide_older_than_hours)
        
        stmt = (
            select(OnlineEvents)
            .where(OnlineEvents.is_active == True)
            .where(OnlineEvents.start_at >= cutoff_time)
            .order_by(OnlineEvents.start_at.asc())
        )
        
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [r.to_model() for r in rows]

    async def is_link_available(self, *, event_id: int, hours_before: int = 1) -> bool:
        """Check if the event link should be available (within N hours before start)."""
        event = await self.get_by_id(id=event_id)
        if not event:
            return False
        
        # Use the datetime formatter helper
        from app.utils.datetime_formatters import is_link_available as check_link_available
        return check_link_available(event.start_at, hours_before=hours_before)

    async def set_active(self, *, slug: str, is_active: bool) -> None:
        """Set event active/inactive status."""
        stmt = update(OnlineEvents).where(OnlineEvents.slug == slug).values(is_active=is_active)
        await self.session.execute(stmt)
        logger.info("Online event active=%s. slug=%s", is_active, slug)
