import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.users import UsersModel, Users

logger = logging.getLogger(__name__)


class _UsersDB:
    __tablename__ = "users"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        *,
        user_id: int,
        roles: list[str] | None = None,
        is_alive: bool = True,
        is_blocked: bool = False,
    ) -> None:
        stmt = (
            insert(Users)
            .values(
                user_id=user_id,
                roles=roles or ["guest"],
                is_alive=is_alive,
                is_blocked=is_blocked,
            )
            .on_conflict_do_nothing(index_elements=[Users.user_id])
        )
        await self.session.execute(stmt)
        logger.info(
            "User added. db='%s', user_id=%d, date_time='%s', is_alive=%s, is_blocked=%s",
            self.__tablename__,
            user_id,
            datetime.now(timezone.utc),
            is_alive,
            is_blocked,
        )

    async def delete(self, *, user_id: int) -> None:
        stmt = delete(Users).where(Users.user_id == user_id)
        await self.session.execute(stmt)
        logger.info("User deleted. db='%s', user_id='%d'", self.__tablename__, user_id)

    async def get_user_record(self, *, user_id: int) -> UsersModel | None:
        stmt = select(Users).where(Users.user_id == user_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None
        return entity.to_model()

    async def update_alive_status(self, *, user_id: int, is_alive: bool = True) -> None:
        stmt = (
            update(Users)
            .where(Users.user_id == user_id)
            .values(is_alive=is_alive)
        )
        await self.session.execute(stmt)
        logger.info(
            "User updated. db='%s', user_id=%d, is_alive=%s",
            self.__tablename__,
            user_id,
            is_alive,
        )

    async def update_user_lang(self, *, user_id: int, user_lang: str) -> None:
        logger.warning(
            "Skipping update_user_lang for user %s: language column removed", user_id
        )

    async def set_submission_status(self, *, user_id: int, status: str) -> None:
        logger.warning(
            "Skipping set_submission_status for user %s: column removed", user_id
        )
    async def get_task_submission_status(self, *, user_id: int, task_number: int) -> bool:
        logger.warning(
            "Returning default task submission status for user %s (task %s): columns removed",
            user_id,
            task_number,
        )
        return False

    async def get_user_roles(self, *, user_id: int) -> list[str]:
        stmt = select(Users.roles).where(Users.user_id == user_id)
        result = await self.session.execute(stmt)
        row = result.first()
        roles = row[0] if row else None
        return roles if roles else ["guest"]

    async def set_user_roles(self, *, user_id: int, roles: list[str], granted_by: int | None = None) -> None:
        stmt = (
            update(Users)
            .where(Users.user_id == user_id)
            .values(roles=roles or ["guest"])
        )
        await self.session.execute(stmt)

        if granted_by:
            logger.info(
                "User roles updated. db='%s', user_id=%d, roles=%s, granted_by=%d",
                self.__tablename__,
                user_id,
                roles,
                granted_by,
            )
        else:
            logger.info(
                "User roles updated. db='%s', user_id=%d, roles=%s",
                self.__tablename__,
                user_id,
                roles,
            )

    async def add_user_role(self, *, user_id: int, role: str, granted_by: int | None = None) -> None:
        current_roles = await self.get_user_roles(user_id=user_id)
        if role not in current_roles:
            current_roles.append(role)
            await self.set_user_roles(user_id=user_id, roles=current_roles, granted_by=granted_by)

    async def remove_user_role(self, *, user_id: int, role: str, revoked_by: int | None = None) -> None:
        current_roles = await self.get_user_roles(user_id=user_id)
        if role in current_roles:
            current_roles.remove(role)
            if not current_roles:
                current_roles = ["guest"]
            await self.set_user_roles(user_id=user_id, roles=current_roles, granted_by=revoked_by)

    async def user_has_role(self, *, user_id: int, role: str) -> bool:
        roles = await self.get_user_roles(user_id=user_id)
        return role in roles

    async def user_has_any_role(self, *, user_id: int, roles: list[str]) -> bool:
        user_roles = await self.get_user_roles(user_id=user_id)
        return bool(set(roles) & set(user_roles))

    async def list_users_by_role(self, *, role: str) -> list[int]:
        result = await self.session.execute(
            text(
                """
                SELECT user_id
                  FROM users
                 WHERE roles ? :role
                   AND is_blocked = FALSE
                """
            ),
            {"role": role},
        )
        return [row.user_id for row in result]
