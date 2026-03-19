"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.main.states import MainMenuSG
from app.bot.dialogs.start_help.states import StartHelpSG
from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.user_info import UsersInfoModel
from app.services.vol_part2_timer import cancel_user_timer

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
# router.message.filter(IsNotBanned())
# router.callback_query.filter(IsNotBanned())


async def _register_via_code(
    db: DB,
    user_id: int,
    username: str | None,
    numeric_key: str,
) -> bool:
    """Attempt to register user via a numeric_key from site_registrations.

    Returns True on success, False if code is invalid or already claimed.
    """
    site_reg = await db.forum_registrations.get_site_registration(numeric_key=numeric_key)
    if site_reg is None:
        return False

    if await db.forum_registrations.is_unique_id_locked(unique_id=site_reg["id"]):
        return False

    await db.forum_registrations.create_registration(
        user_id=user_id,
        unique_id=site_reg["id"],
        site_reg=site_reg,
    )
    await db.users_info.upsert(
        model=UsersInfoModel(
            user_id=user_id,
            full_name=site_reg.get("full_name"),
            email=site_reg.get("email"),
            username=username,
            education=site_reg.get("education"),
        )
    )
    return True


@router.message(CommandStart())
async def start_command(message: Message, command: CommandStart, dialog_manager: DialogManager):
    """Команда /start — routing based on forum registration state."""
    user = message.from_user
    payload = command.args or ""

    cancel_user_timer(user.id)

    logger.debug("User id=%s reached /start, payload=%r", user.id, payload)

    db: DB | None = dialog_manager.middleware_data.get("db")

    # ── Scenario 0: already registered ───────────────────────────────────────
    if db:
        try:
            existing = await db.forum_registrations.get_by_user_id(user_id=user.id)
            if existing:
                await dialog_manager.start(state=MainMenuSG.MAIN, mode=StartMode.RESET_STACK)
                return
        except Exception as exc:
            logger.error("Error checking forum registration for user_id=%s: %s", user.id, exc)

    # ── Scenario 1: deeplink with reg- code ───────────────────────────────────
    if payload.startswith("reg-"):
        numeric_key = payload[4:]
        if db:
            try:
                success = await _register_via_code(
                    db=db,
                    user_id=user.id,
                    username=user.username,
                    numeric_key=numeric_key,
                )
                if success:
                    logger.info(
                        "User id=%s registered via deeplink code=%s", user.id, numeric_key
                    )
                    await message.answer(
                        "✅ Регистрация прошла успешно! Ждем тебя на форуме КБК'26 11 апреля! "
                        "А пока можешь ознакомиться с деталями форума в боте."
                    )
                    await dialog_manager.start(state=MainMenuSG.MAIN, mode=StartMode.RESET_STACK)
                    return
                else:
                    logger.info(
                        "Deeplink code invalid/locked for user_id=%s code=%s",
                        user.id,
                        numeric_key,
                    )
            except Exception as exc:
                logger.error(
                    "Error processing deeplink for user_id=%s code=%s: %s",
                    user.id,
                    numeric_key,
                    exc,
                )

    # ── Scenario 2: not registered, no valid deeplink ─────────────────────────
    await dialog_manager.start(state=StartHelpSG.want_reg, mode=StartMode.RESET_STACK)


@router.message(Command("menu"))
async def menu_command(message: Message, dialog_manager: DialogManager):
    """Команда /menu - переход в главное меню"""
    cancel_user_timer(message.from_user.id)
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

