from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.feedback import Feedback, FeedbackModel


class _FeedbackDB:
    """Read-only access to aggregated legacy feedback data."""

    __tablename__ = Feedback.__tablename__

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_feedback(self, *, user_id: int) -> FeedbackModel | None:
        stmt = select(Feedback).where(Feedback.user_id == user_id)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()
