"""
Хендлеры для запуска диалогов волонтёров
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.filters.rbac import HasRole
from app.enums.roles import Role
from app.bot.dialogs.volunteer.states import VolunteerMenuSG

logger = logging.getLogger(__name__)

volunteer_dialogs_router = Router(name="volunteer_dialogs")

# Фильтр для волонтёров и ролей выше
volunteer_dialogs_router.message.filter(HasRole(Role.VOLUNTEER, Role.STAFF, Role.ADMIN))


@volunteer_dialogs_router.message(F.text.in_(["/start", "/menu"]))
async def start_volunteer_menu(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """
    Запуск главного меню для волонтёров
    Срабатывает если у пользователя роль volunteer (но не staff/admin)
    """
    roles = roles or set()
    
    # Проверяем что это волонтёр, но не сотрудник/админ
    if Role.VOLUNTEER.value in roles and not any(role in roles for role in [Role.STAFF.value, Role.ADMIN.value]):
        logger.info(f"Starting volunteer menu for user {message.from_user.id}")
        await dialog_manager.start(
            VolunteerMenuSG.MAIN,
            mode=StartMode.RESET_STACK
        )