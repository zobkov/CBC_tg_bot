"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.volunteer.states import VolunteerMenuSG  
from app.bot.dialogs.staff.states import StaffMenuSG
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
# router.message.filter(IsNotBanned())
# router.callback_query.filter(IsNotBanned())


@router.message(Command("start"))
async def start_command(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """Команда /start - запуск диалога приветствия в зависимости от роли"""
    roles = roles or set()
    
    # Определяем состояние диалога в зависимости от роли пользователя
    if Role.ADMIN.value in roles or Role.STAFF.value in roles:
        await dialog_manager.start(state=StaffMenuSG.MAIN, mode=StartMode.RESET_STACK)
    elif Role.VOLUNTEER.value in roles:
        await dialog_manager.start(state=VolunteerMenuSG.MAIN, mode=StartMode.RESET_STACK)
    else:
        # Гости и все остальные (включая новых пользователей)
        await dialog_manager.start(state=GuestMenuSG.MAIN, mode=StartMode.RESET_STACK)


@router.message(Command("menu"))
async def menu_command(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """Команда /menu - переход в главное меню в зависимости от роли"""
    roles = roles or set()
    
    # Определяем состояние диалога в зависимости от роли пользователя
    if Role.ADMIN.value in roles or Role.STAFF.value in roles:
        await dialog_manager.start(state=StaffMenuSG.MAIN, mode=StartMode.RESET_STACK)
    elif Role.VOLUNTEER.value in roles:
        await dialog_manager.start(state=VolunteerMenuSG.MAIN, mode=StartMode.RESET_STACK)
    else:
        # Гости и все остальные
        await dialog_manager.start(state=GuestMenuSG.MAIN, mode=StartMode.RESET_STACK)



@router.message(Command("whoami"))
async def whoami_command(message: Message, current_user=None, roles: set[str] = None):
    """Информация о пользователе и его ролях"""
    roles = roles or set()
    user_id = message.from_user.id
    username = message.from_user.username or "не установлен"
    
    roles_list = ", ".join(sorted(roles)) if roles else "нет ролей"
    
    info_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Username: @{username}\n"
        f"🏷 Роли: {roles_list}\n"
    )
    
    if current_user:
        if hasattr(current_user.created, 'strftime'):
            created_str = current_user.created.strftime('%d.%m.%Y %H:%M')
        else:
            created_str = str(current_user.created)

        alive_text = "активен" if current_user.is_alive else "не активен"
        blocked_text = "заблокирован" if current_user.is_blocked else "доступен"
        roles_details = ", ".join(sorted(set(current_user.roles)))

        info_text += (
            f"📅 Регистрация: {created_str}\n"
            f"🛡️ Статус: {alive_text}, {blocked_text}\n"
            f"🎭 Роли: {roles_details}\n"
        )
    
    await message.answer(info_text)

