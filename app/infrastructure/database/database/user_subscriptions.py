import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user_subscriptions import UserSubscriptionModel, UserSubscriptions
from app.infrastructure.database.models.broadcasts import Broadcasts

logger = logging.getLogger(__name__)


class _UserSubscriptionsDB:
    __tablename__ = "user_subscriptions"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def subscribe_by_broadcast_key(self, *, user_id: int, broadcast_key: str) -> None:
        # Resolve broadcast id
        result = await self.session.execute(select(Broadcasts).where(Broadcasts.key == broadcast_key))
        b = result.scalar_one_or_none()
        if b is None:
            raise ValueError(f"Unknown broadcast key: {broadcast_key}")

        stmt = (
            insert(UserSubscriptions)
            .values(user_id=user_id, broadcast_id=b.id)
            .on_conflict_do_update(
                index_elements=[UserSubscriptions.user_id, UserSubscriptions.broadcast_id],
                set_={
                    "unsubscribed_at": None,
                    "subscribed_at": text("TIMEZONE('utc', NOW())"),
                },
            )
        )

        await self.session.execute(stmt)
        logger.info("User %s subscribed to %s", user_id, broadcast_key)

    async def unsubscribe(self, *, user_id: int, broadcast_key: str) -> None:
        # Resolve broadcast id
        result = await self.session.execute(select(Broadcasts).where(Broadcasts.key == broadcast_key))
        b = result.scalar_one_or_none()
        if b is None:
            return

        stmt = (
            update(UserSubscriptions)
            .where(UserSubscriptions.user_id == user_id)
            .where(UserSubscriptions.broadcast_id == b.id)
            .values(unsubscribed_at=text("TIMEZONE('utc', NOW())"))
        )
        await self.session.execute(stmt)
        logger.info("User %s unsubscribed from %s", user_id, broadcast_key)

    async def list_subscribers(self, *, broadcast_key: str, limit: int | None = None) -> list[int]:
        sql = text(
            """
            SELECT u.user_id
              FROM users u
              JOIN user_subscriptions s ON s.user_id = u.user_id
              JOIN broadcasts b ON b.id = s.broadcast_id
             WHERE b.key = :key
               AND s.unsubscribed_at IS NULL
               AND b.enabled = TRUE
               AND u.is_alive = TRUE
            """
        )
        params = {"key": broadcast_key}
        if limit:
            sql = text(sql.text + " LIMIT :limit")
            params["limit"] = limit

        result = await self.session.execute(sql, params)
        return [row.user_id for row in result]

    async def get_user_subscriptions(self, *, user_id: int) -> list[UserSubscriptionModel]:
        result = await self.session.execute(select(UserSubscriptions).where(UserSubscriptions.user_id == user_id))
        rows = result.scalars().all()
        return [r.to_model() for r in rows]
