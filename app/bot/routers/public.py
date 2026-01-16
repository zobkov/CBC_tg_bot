"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.volunteer.states import VolunteerMenuSG  
from app.bot.dialogs.staff.states import StaffMenuSG
from app.enums.roles import Role
from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
# router.message.filter(IsNotBanned())
# router.callback_query.filter(IsNotBanned())


@router.message(CommandStart())
async def start_command(message: Message, command: CommandStart, dialog_manager: DialogManager, roles: set[str] = None):
    """Команда /start - запуск диалога приветствия в зависимости от роли"""
    payload = command.args
    if payload == "sub_vol":
        BROADCAST_KEY = "volunteer_selection"

        db: DB | None = dialog_manager.middleware_data.get("db")
        event = getattr(dialog_manager, "event", None)
        user = getattr(event, "from_user", None) if event else None

        try:
            await db.user_subscriptions.subscribe_by_broadcast_key(user_id = user.id, broadcast_key = BROADCAST_KEY)

            await message.answer("✅ Подписка на рассылку новостей об отоборе волонтёров активна!\n\nУправлять разрешениями на рассылку можно в соответвующем меню.")
        except Exception as e:
            logger.error("Error while auto subscribing user id=%s : %s", user.id, e)
            

    roles = roles or set()
    
    logger.debug("User id=%s has reached /start handler", message.from_user.id)

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

