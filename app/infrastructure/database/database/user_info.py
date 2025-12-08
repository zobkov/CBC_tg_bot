import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user_info import UserInfoModel, UserInfo

logger = logging.getLogger(__name__)

class _UserInfoDB:
    __tablename__ = "user_info"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_info: UserInfo) -> None:  # adds user info  
        NotImplemented

    async def delete(self, user_id: int) -> None: # delete the whole user info entry 
        NotImplemented

    async def get_user_info(self, user_id: int) -> UserInfoModel | None: # get user info entry 
        NotImplemented


