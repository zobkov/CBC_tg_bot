import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.online_registrations import OnlineRegistrationModel, OnlineRegistrations
from app.infrastructure.database.models.online_events import OnlineEvents

logger = logging.getLogger(__name__)


class _OnlineRegistrationsDB:
    __tablename__ = "online_registrations"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, *, user_id: int, event_id: int) -> None:
        """Register user for an event. Reactivates if previously cancelled."""
        stmt = (
            insert(OnlineRegistrations)
            .values(user_id=user_id, event_id=event_id, status="active")
            .on_conflict_do_update(
                index_elements=[OnlineRegistrations.user_id, OnlineRegistrations.event_id],
                set_={
                    "status": "active",
                    "registered_at": text("TIMEZONE('utc', NOW())"),
                },
            )
        )
        await self.session.execute(stmt)
        logger.info("User %s registered for event %s", user_id, event_id)

    async def cancel(self, *, user_id: int, event_id: int) -> None:
        """Cancel user registration for an event."""
        stmt = (
            update(OnlineRegistrations)
            .where(OnlineRegistrations.user_id == user_id)
            .where(OnlineRegistrations.event_id == event_id)
            .values(status="cancelled")
        )
        await self.session.execute(stmt)
        logger.info("User %s cancelled registration for event %s", user_id, event_id)

    async def check_registration_status(self, *, user_id: int, event_id: int) -> str | None:
        """Check if user is registered for an event. Returns status or None."""
        stmt = (
            select(OnlineRegistrations.status)
            .where(OnlineRegistrations.user_id == user_id)
            .where(OnlineRegistrations.event_id == event_id)
        )
        result = await self.session.execute(stmt)
        status = result.scalar_one_or_none()
        return status

    async def get_user_registrations(self, *, user_id: int, active_only: bool = True) -> list[OnlineRegistrationModel]:
        """Get all registrations for a user."""
        stmt = select(OnlineRegistrations).where(OnlineRegistrations.user_id == user_id)
        
        if active_only:
            stmt = stmt.where(OnlineRegistrations.status == "active")
        
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [r.to_model() for r in rows]

    async def get_event_registrations(self, *, event_id: int, active_only: bool = True) -> list[OnlineRegistrationModel]:
        """Get all registrations for an event."""
        stmt = select(OnlineRegistrations).where(OnlineRegistrations.event_id == event_id)
        
        if active_only:
            stmt = stmt.where(OnlineRegistrations.status == "active")
        
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [r.to_model() for r in rows]

    async def get_registration_with_event_details(self, *, user_id: int) -> list[dict]:
        """Get user registrations with joined event details."""
        sql = text(
            """
            SELECT 
                r.id as registration_id,
                r.status,
                r.registered_at,
                e.id as event_id,
                e.slug,
                e.alias,
                e.title,
                e.speaker,
                e.description,
                e.url,
                e.start_at,
                e.end_at
            FROM online_registrations r
            JOIN online_events e ON e.id = r.event_id
            WHERE r.user_id = :user_id
              AND r.status = 'active'
              AND e.is_active = TRUE
            ORDER BY e.start_at ASC
            """
        )
        result = await self.session.execute(sql, {"user_id": user_id})
        return [dict(row._mapping) for row in result]
