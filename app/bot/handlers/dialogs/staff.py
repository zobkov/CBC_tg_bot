"""
Хендлеры для запуска диалогов сотрудников
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.filters.rbac import HasRole
from app.enums.roles import Role
from app.bot.dialogs.staff.states import StaffMenuSG

logger = logging.getLogger(__name__)

staff_dialogs_router = Router(name="staff_dialogs")

# Фильтр для сотрудников и админов
staff_dialogs_router.message.filter(HasRole(Role.STAFF, Role.ADMIN))


@staff_dialogs_router.message(F.text.in_(["/start", "/menu"]))
async def start_staff_menu(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """
    Запуск главного меню для сотрудников
    Срабатывает если у пользователя роль staff (но не admin)
    """
    roles = roles or set()
    
    # Проверяем что это сотрудник, но не админ
    if Role.STAFF.value in roles and Role.ADMIN.value not in roles:
        logger.info(f"Starting staff menu for user {message.from_user.id}")
        await dialog_manager.start(
            StaffMenuSG.MAIN,
            mode=StartMode.RESET_STACK
        )