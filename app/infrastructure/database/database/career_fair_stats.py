"""DAO for career fair click/view statistics."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.career_fair_stats import CareerFairEvent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TrackStat:
    track_key: str
    total_views: int
    unique_users: int


@dataclass(slots=True)
class CompanyStat:
    company_key: str
    track_key: str | None
    total_views: int
    unique_users: int
    vacancies_views: int


class _CareerFairStatsDB:
    __tablename__ = "career_fair_events"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def log_event(
        self,
        *,
        user_id: int,
        event_type: str,
        track_key: str | None = None,
        company_key: str | None = None,
    ) -> None:
        """Insert a single analytics event row."""
        event = CareerFairEvent(
            user_id=user_id,
            event_type=event_type,
            track_key=track_key,
            company_key=company_key,
        )
        self.session.add(event)
        logger.debug(
            "career_fair event logged: user=%d type=%s track=%s company=%s",
            user_id,
            event_type,
            track_key,
            company_key,
        )

    # ------------------------------------------------------------------
    # Read / aggregations
    # ------------------------------------------------------------------

    async def get_track_stats(self) -> list[TrackStat]:
        """Return view counts per track (only 'track_view' events)."""
        stmt = (
            select(
                CareerFairEvent.track_key,
                func.count(CareerFairEvent.id).label("total_views"),
                func.count(func.distinct(CareerFairEvent.user_id)).label("unique_users"),
            )
            .where(CareerFairEvent.event_type == "track_view")
            .where(CareerFairEvent.track_key.isnot(None))
            .group_by(CareerFairEvent.track_key)
            .order_by(func.count(CareerFairEvent.id).desc())
        )
        result = await self.session.execute(stmt)
        return [
            TrackStat(
                track_key=row.track_key,
                total_views=row.total_views,
                unique_users=row.unique_users,
            )
            for row in result.all()
        ]

    async def get_company_stats(self) -> list[CompanyStat]:
        """Return view and vacancies-open counts per company."""
        # Company page views
        views_stmt = (
            select(
                CareerFairEvent.company_key,
                CareerFairEvent.track_key,
                func.count(CareerFairEvent.id).label("total_views"),
                func.count(func.distinct(CareerFairEvent.user_id)).label("unique_users"),
            )
            .where(CareerFairEvent.event_type == "company_view")
            .where(CareerFairEvent.company_key.isnot(None))
            .group_by(CareerFairEvent.company_key, CareerFairEvent.track_key)
        )
        views_result = await self.session.execute(views_stmt)
        views_by_company = {
            row.company_key: (row.track_key, row.total_views, row.unique_users)
            for row in views_result.all()
        }

        # Vacancies opens
        vac_stmt = (
            select(
                CareerFairEvent.company_key,
                func.count(CareerFairEvent.id).label("vac_views"),
            )
            .where(CareerFairEvent.event_type == "vacancies_view")
            .where(CareerFairEvent.company_key.isnot(None))
            .group_by(CareerFairEvent.company_key)
        )
        vac_result = await self.session.execute(vac_stmt)
        vac_by_company = {row.company_key: row.vac_views for row in vac_result.all()}

        all_keys = set(views_by_company) | set(vac_by_company)
        stats = []
        for key in all_keys:
            track_key, total_views, unique_users = views_by_company.get(key, (None, 0, 0))
            stats.append(
                CompanyStat(
                    company_key=key,
                    track_key=track_key,
                    total_views=total_views,
                    unique_users=unique_users,
                    vacancies_views=vac_by_company.get(key, 0),
                )
            )

        stats.sort(key=lambda s: s.total_views, reverse=True)
        return stats
