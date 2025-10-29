"""
Хендлеры для запуска диалогов гостей
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.filters.rbac import HasRole
from app.enums.roles import Role
from app.bot.dialogs.guest.states import GuestMenuSG

logger = logging.getLogger(__name__)

guest_dialogs_router = Router(name="guest_dialogs")

# Фильтр для гостей и всех ролей выше
guest_dialogs_router.message.filter(HasRole(Role.GUEST, Role.VOLUNTEER, Role.STAFF, Role.ADMIN))


@guest_dialogs_router.message(F.text.in_(["/start", "/menu"]))
async def start_guest_menu(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """
    Запуск главного меню для гостей
    Срабатывает только если у пользователя роль guest (и нет более высоких ролей)
    """
    roles = roles or set()
    
    # Проверяем что это именно гость (не staff/admin)
    if not any(role in roles for role in [Role.ADMIN.value, Role.STAFF.value, Role.VOLUNTEER.value]):
        logger.info(f"Starting guest menu for user {message.from_user.id}")
        await dialog_manager.start(
            GuestMenuSG.MAIN,
            mode=StartMode.RESET_STACK
        )
    # Если у пользователя есть более высокие роли, пропускаем
    # (сработают обработчики с более высоким приоритетом)