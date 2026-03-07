"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.main.states import MainMenuSG
from app.bot.dialogs.registration.states import RegistrationSG
from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
# router.message.filter(IsNotBanned())
# router.callback_query.filter(IsNotBanned())


@router.message(CommandStart())
async def start_command(message: Message, command: CommandStart, dialog_manager: DialogManager):
    """Команда /start - запуск диалога приветствия"""
    payload = command.args
    if payload == "sub_vol":
        BROADCAST_KEY = "volunteer_selection"

        db: DB | None = dialog_manager.middleware_data.get("db")
        event = getattr(dialog_manager, "event", None)
        user = getattr(event, "from_user", None) if event else None

        try:
            await db.user_subscriptions.subscribe_by_broadcast_key(user_id=user.id, broadcast_key=BROADCAST_KEY)
            await message.answer("✅ Подписка на рассылку новостей об отоборе волонтёров активна!\n\nУправлять разрешениями на рассылку можно в соответвующем меню.")
        except Exception as e:
            logger.error("Error while auto subscribing user id=%s : %s", user.id, e)

    logger.debug("User id=%s has reached /start handler", message.from_user.id)

    # Проверяем регистрацию пользователя
    db: DB | None = dialog_manager.middleware_data.get("db")
    is_registered = False

    if db:
        try:
            user_info = await db.users_info.get_user_info(user_id=message.from_user.id)
            if user_info and user_info.full_name and user_info.email:
                is_registered = True
        except Exception as e:
            logger.error("Error checking registration status: %s", e)

    if is_registered:
        await dialog_manager.start(state=MainMenuSG.MAIN, mode=StartMode.RESET_STACK)
    else:
        await dialog_manager.start(state=RegistrationSG.MAIN, mode=StartMode.RESET_STACK)


@router.message(Command("menu"))
async def menu_command(message: Message, dialog_manager: DialogManager):
    """Команда /menu - переход в главное меню"""
    await dialog_manager.start(state=MainMenuSG.MAIN, mode=StartMode.RESET_STACK)



@router.message(Command("whoami"))
async def whoami_command(message: Message):
    """Информация о пользователе"""
    user_id = message.from_user.id
    username = message.from_user.username or "не установлен"
    info_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Username: @{username}\n"
    )
    await message.answer(info_text)

