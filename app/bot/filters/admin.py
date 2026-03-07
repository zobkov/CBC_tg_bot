"""Admin filters"""

import logging

from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter

logger = logging.getLogger(__name__)

class AdminFilter(Filter):
    """Admin filter. Returns bool when calle. Takes admin_ids list at init"""
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        is_admin = message.from_user.id in self.admin_ids
        logger.debug("Admin filter check: user_id=%s, is_admin=%s",
                     message.from_user.id, is_admin)
        return is_admin
