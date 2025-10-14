"""
Хендлеры для запуска диалогов администраторов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.filters.rbac import HasRole
from app.enums.roles import Role
from app.bot.dialogs.staff.states import StaffMenuSG  # Используем тот же диалог что и у staff

logger = logging.getLogger(__name__)

admin_dialogs_router = Router(name="admin_dialogs")

# Фильтр только для админов
admin_dialogs_router.message.filter(HasRole(Role.ADMIN))


@admin_dialogs_router.message(F.text.in_(["/start", "/menu"]))
async def start_admin_menu(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """
    Запуск главного меню для администраторов
    Используем тот же диалог что и для сотрудников, но с расширенными правами
    """
    roles = roles or set()
    
    if Role.ADMIN.value in roles:
        logger.info(f"Starting admin menu for user {message.from_user.id}")
        await dialog_manager.start(
            StaffMenuSG.MAIN,  # Админы используют тот же диалог что и staff
            mode=StartMode.RESET_STACK
        )