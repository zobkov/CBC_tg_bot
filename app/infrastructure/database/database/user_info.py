import logging

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user_info import UsersInfoModel, UsersInfo

logger = logging.getLogger(__name__)

class _UsersInfoDB:
    __tablename__ = "user_info"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, *, model: UsersInfoModel) -> None:
        normalized = model.normalized_copy()
        payload = normalized.as_db_payload()
        payload.pop("id", None)
        payload.pop("created", None)
        payload.pop("updated", None)

        stmt = insert(UsersInfo).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[UsersInfo.user_id],
            set_=payload,
        )
        await self.session.execute(stmt)
        logger.info(
            "User info saved. db='%s', user_id=%d",
            self.__tablename__,
            normalized.user_id,
        )

    async def delete(self, *, user_id: int) -> None:
        stmt = delete(UsersInfo).where(UsersInfo.user_id == user_id)
        result = await self.session.execute(stmt)
        if result.rowcount:
            logger.info("User info deleted. db='%s', user_id=%d", self.__tablename__, user_id)
        else:
            logger.debug("User info delete skipped (missing). db='%s', user_id=%d", self.__tablename__, user_id)

    async def get_user_info(self, *, user_id: int) -> UsersInfoModel | None:
        stmt = select(UsersInfo).where(UsersInfo.user_id == user_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()


