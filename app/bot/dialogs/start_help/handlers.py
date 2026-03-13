"""Handlers for the start_help onboarding dialog."""

from __future__ import annotations

import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from app.bot.dialogs.main.states import MainMenuSG
from app.bot.dialogs.start_help.states import StartHelpSG
from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.user_info import UsersInfoModel

logger = logging.getLogger(__name__)


# ── Button callbacks ──────────────────────────────────────────────────────────

async def on_yes_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """User wants to register → ask if they already visited the site."""
    await callback.answer()
    await dialog_manager.switch_to(StartHelpSG.site_reg)


async def on_no_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """User does not want to register → go to main menu."""
    await callback.answer()
    await dialog_manager.start(MainMenuSG.MAIN, mode=StartMode.RESET_STACK)


async def on_has_reg_yes(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """User confirms they registered on the site → ask for the code."""
    await callback.answer()
    await dialog_manager.switch_to(StartHelpSG.id_enter)


async def on_has_reg_no(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """User hasn't registered on the site → show instructions."""
    await callback.answer()
    await dialog_manager.switch_to(StartHelpSG.need_reg)


async def on_has_code_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """User already has a code → go to code entry."""
    await callback.answer()
    await dialog_manager.switch_to(StartHelpSG.id_enter)


# ── TextInput validator + handlers ────────────────────────────────────────────

def code_check(value: str) -> str:
    """Validate that the entered value is exactly 6 digits."""
    stripped = value.strip()
    if not stripped.isdigit() or len(stripped) != 6:
        raise ValueError("Код должен состоять из 6 цифр. Попробуй ещё раз.")
    return stripped


async def code_error_handler(
    message: Message,
    _dialog: Any,
    _manager: DialogManager,
    error: ValueError,
) -> None:
    await message.answer(str(error))


async def on_code_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Validate the code against site_registrations and register the user if valid."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    if db is None:
        logger.error("on_code_entered: db not found in middleware_data")
        await message.answer("Произошла ошибка. Попробуй позже.")
        return

    user = message.from_user

    # 1. Look up site registration by numeric key
    site_reg = await db.forum_registrations.get_site_registration(numeric_key=value)
    if site_reg is None:
        logger.info("Code lookup failed: numeric_key=%s user_id=%s", value, user.id)
        await dialog_manager.switch_to(StartHelpSG.wrong_code)
        return

    # 2. Check the unique_id is not already claimed by another account
    if await db.forum_registrations.is_unique_id_locked(unique_id=site_reg["id"]):
        logger.info(
            "Code already locked: numeric_key=%s unique_id=%s user_id=%s",
            value,
            site_reg["id"],
            user.id,
        )
        await dialog_manager.switch_to(StartHelpSG.wrong_code)
        return

    # 3. Create bot_forum_registrations entry
    await db.forum_registrations.create_registration(
        user_id=user.id,
        unique_id=site_reg["id"],
        site_reg=site_reg,
    )

    # 4. Upsert user_info
    await db.users_info.upsert(
        model=UsersInfoModel(
            user_id=user.id,
            full_name=site_reg.get("full_name"),
            email=site_reg.get("email"),
            username=user.username,
            education=site_reg.get("education"),
        )
    )

    logger.info("Forum registration complete for user_id=%s", user.id)
    await message.answer(
        "✅ Регистрация прошла успешно! Ждем тебя на форуме КБК'26 11 апреля! "
        "А пока можешь ознакомиться с деталями форума в боте."
    )
    await dialog_manager.start(MainMenuSG.MAIN, mode=StartMode.RESET_STACK)
