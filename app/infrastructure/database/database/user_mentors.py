import logging

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user_mentors import UserMentors, UserMentorsModel

logger = logging.getLogger(__name__)


class _UserMentorsDB:
    __tablename__ = "user_mentors"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, *, user_id: int) -> UserMentorsModel | None:
        """Return the user_mentors record for *user_id*, or *None*."""
        stmt = select(UserMentors).where(UserMentors.user_id == user_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()

    async def upsert(
        self,
        *,
        user_id: int,
        mentor_contacts: str | None = None,
    ) -> None:
        """Create a record for *user_id* if it does not exist, or update
        *mentor_contacts* if it does.  Leaves *lessons_approved* untouched on
        conflict so that existing unlocks are preserved.
        """
        stmt = (
            insert(UserMentors)
            .values(
                user_id=user_id,
                mentor_contacts=mentor_contacts,
                lessons_approved=[],
            )
            .on_conflict_do_update(
                index_elements=[UserMentors.user_id],
                set_={"mentor_contacts": mentor_contacts},
            )
        )
        await self.session.execute(stmt)
        logger.info(
            "user_mentors upserted. user_id=%d, mentor_contacts=%s",
            user_id,
            mentor_contacts,
        )

    async def approve_lesson(self, *, user_id: int, tag: str) -> bool:
        """Append *tag* to *lessons_approved* for *user_id*.

        Returns *True* if the tag was newly added, *False* if it was already
        present or if the user record does not exist.
        """
        stmt = select(UserMentors).where(UserMentors.user_id == user_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()

        if entity is None:
            logger.warning(
                "approve_lesson: no record for user_id=%d — tag '%s' not added",
                user_id,
                tag,
            )
            return False

        approved: list[str] = list(entity.lessons_approved or [])
        if tag in approved:
            logger.info(
                "approve_lesson: tag '%s' already approved for user_id=%d",
                tag,
                user_id,
            )
            return False

        approved.append(tag)
        await self.session.execute(
            update(UserMentors)
            .where(UserMentors.user_id == user_id)
            .values(lessons_approved=approved)
        )
        logger.info(
            "approve_lesson: tag '%s' added for user_id=%d",
            tag,
            user_id,
        )
        return True
