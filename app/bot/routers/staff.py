"""
Роутер для сотрудников (staff)
"""
import logging
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.bot.filters.legacy_intents import create_rbac_filter_with_legacy_exclusion
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="staff")

# Фильтр для сотрудников и админов с исключением legacy интентов
staff_filter = create_rbac_filter_with_legacy_exclusion(Role.STAFF, Role.ADMIN)
router.message.filter(staff_filter)
router.callback_query.filter(staff_filter)

