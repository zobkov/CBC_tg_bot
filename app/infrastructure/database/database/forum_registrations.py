"""SQLAlchemy Core access layer for bot_forum_registrations and site_registrations."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class _ForumRegistrationsDB:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, *, user_id: int) -> dict | None:
        """Return bot_forum_registrations row for the given Telegram user, or None."""
        result = await self.session.execute(
            text(
                "SELECT id, user_id, unique_id, name, status "
                "FROM bot_forum_registrations "
                "WHERE user_id = :user_id "
                "LIMIT 1"
            ),
            {"user_id": user_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_site_registration(self, *, numeric_key: str) -> dict | None:
        """Return site_registrations row matching the 6-digit numeric_key, or None."""
        result = await self.session.execute(
            text(
                "SELECT id, full_name, status, email, adult18, region, "
                "participant_status, education, track, transport, car_number, passport "
                "FROM site_registrations "
                "WHERE numeric_key = :numeric_key "
                "LIMIT 1"
            ),
            {"numeric_key": numeric_key},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def is_unique_id_locked(self, *, unique_id: str) -> bool:
        """Return True if this site_registration UUID is already claimed by a Telegram account."""
        result = await self.session.execute(
            text(
                "SELECT 1 FROM bot_forum_registrations "
                "WHERE unique_id = :unique_id "
                "LIMIT 1"
            ),
            {"unique_id": unique_id},
        )
        return result.first() is not None

    async def create_registration(
        self,
        *,
        user_id: int,
        unique_id: str,
        site_reg: dict,
    ) -> None:
        """Insert a bot_forum_registrations row from site_registrations data.

        Uses ON CONFLICT DO NOTHING so a duplicate call (e.g. double-tap deeplink)
        is silently ignored.
        """
        await self.session.execute(
            text(
                """
                INSERT INTO bot_forum_registrations
                    (user_id, unique_id, name, status, adult18, region,
                     occupation_status, education, track, transport, car_number, passport)
                VALUES
                    (:user_id, :unique_id, :name, :status, :adult18, :region,
                     :occupation_status, :education, :track, :transport, :car_number, :passport)
                ON CONFLICT (user_id) DO NOTHING
                """
            ),
            {
                "user_id": user_id,
                "unique_id": unique_id,
                "name": site_reg.get("full_name"),
                "status": site_reg.get("status"),
                "adult18": site_reg.get("adult18"),
                "region": site_reg.get("region"),
                "occupation_status": site_reg.get("participant_status"),
                "education": site_reg.get("education"),
                "track": site_reg.get("track"),
                "transport": site_reg.get("transport"),
                "car_number": site_reg.get("car_number"),
                "passport": site_reg.get("passport"),
            },
        )
        logger.info(
            "bot_forum_registrations: created entry for user_id=%d, unique_id=%s",
            user_id,
            unique_id,
        )
