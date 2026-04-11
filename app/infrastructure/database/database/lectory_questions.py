"""DAO for lectory event Q&A questions."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.lectory_questions import LectoryQuestion

logger = logging.getLogger(__name__)


class _LectoryQuestionsDB:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_question(
        self,
        *,
        user_id: int,
        event_key: str,
        event_name: str,
        question_text: str,
    ) -> LectoryQuestion:
        """Insert a new question row and return it."""
        q = LectoryQuestion(
            user_id=user_id,
            event_key=event_key,
            event_name=event_name,
            question_text=question_text,
        )
        self.session.add(q)
        await self.session.flush()
        logger.debug(
            "lectory_question added: user=%d event=%s question_id=%d",
            user_id,
            event_key,
            q.id,
        )
        return q

    async def get_user_questions_for_event(
        self,
        *,
        user_id: int,
        event_key: str,
    ) -> list[dict[str, Any]]:
        """Return all questions the user submitted for a specific event."""
        stmt = (
            select(LectoryQuestion)
            .where(
                LectoryQuestion.user_id == user_id,
                LectoryQuestion.event_key == event_key,
            )
            .order_by(LectoryQuestion.created_at)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "question_text": r.question_text,
                "answer_text": r.answer_text,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    async def get_all_user_questions(
        self,
        *,
        user_id: int,
    ) -> list[dict[str, Any]]:
        """Return all questions submitted by a user across all events."""
        stmt = (
            select(LectoryQuestion)
            .where(LectoryQuestion.user_id == user_id)
            .order_by(LectoryQuestion.event_key, LectoryQuestion.created_at)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "event_key": r.event_key,
                "event_name": r.event_name,
                "question_text": r.question_text,
                "answer_text": r.answer_text,
                "created_at": r.created_at,
            }
            for r in rows
        ]
