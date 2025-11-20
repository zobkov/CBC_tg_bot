"""
Роутер для гостей (обычные пользователи)
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters.legacy_intents import create_rbac_filter_with_legacy_exclusion
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="guest")

# Фильтр для гостей и всех ролей выше с исключением legacy интентов
guest_filter = create_rbac_filter_with_legacy_exclusion(Role.GUEST, Role.VOLUNTEER, Role.STAFF, Role.ADMIN)
router.message.filter(guest_filter)
router.callback_query.filter(guest_filter)


@router.message()
async def guest_forbidden_handler(message: Message):
    """Обработчик для недоступных гостям команд"""
    await message.answer(
        "⚠️ <b>Команда недоступна</b>\n\n"
        "Данная команда недоступна для вашего уровня доступа.\n\n"
        "Доступные команды:\n"
        "• /start - Главное меню\n"
        "• /apply - Подать заявку\n"
        "• /status - Статус заявки\n"
        "• /support - Техподдержка\n"
        "• /help - Справка"
    )