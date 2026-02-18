"""Callback handlers and validators for registration dialog."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from better_profanity import profanity

from app.bot.dialogs.guest.states import GuestMenuSG
from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.user_info import UsersInfoModel

from app.bot.dialogs.guest.quiz_dod.profanity_list import RUSSIAN_PROFANITY

logger = logging.getLogger(__name__)

# Email validation regex
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@lru_cache(maxsize=1)
def _load_profanity_words() -> None:
    """Load profanity dictionaries only once per process."""
    profanity.load_censor_words()
    profanity.add_censor_words(RUSSIAN_PROFANITY)


def _ensure_profanity_loaded() -> None:
    """Ensure profanity dictionaries are loaded."""
    _load_profanity_words()


# Validation functions (type factories)

def name_check(value: str) -> str:
    """Validate and sanitize the participant's name."""
    _ensure_profanity_loaded()
    name = value.strip()

    if not name:
        raise ValueError("Имя не может быть пустым")
    if len(name) < 2:
        raise ValueError("Имя должно содержать минимум 2 символа")
    if profanity.contains_profanity(name):
        raise ValueError("Имя не может содержать нецензурных выражений!")
    
    return name


def university_check(value: str) -> str:
    """Validate text describing the participant's education."""
    education = value.strip()

    if not education:
        raise ValueError(
            "Поле не может быть пустым. Пожалуйста, укажи учебное заведение и курс."
        )
    if len(education) < 3:
        raise ValueError(
            "Укажи, пожалуйста, полное название учебного заведения и курс/год выпуска."
        )

    return education


def email_check(value: str) -> str:
    """Normalize e-mail to lowercase and validate syntax."""
    email = value.strip().lower()

    if not EMAIL_PATTERN.match(email):
        raise ValueError("Некорректный формат email")

    return email


# Error handlers

async def name_error_handler(
    message: Message,
    _dialog: Any,
    _manager: DialogManager,
    error_: ValueError,
) -> None:
    """Notify user when the entered name is invalid."""
    await message.answer(str(error_))


async def university_error_handler(
    message: Message,
    _dialog: Any,
    _manager: DialogManager,
    error_: ValueError,
) -> None:
    """Notify user when the entered education text is invalid."""
    await message.answer(str(error_))


async def email_error_handler(
    message: Message,
    _dialog: Any,
    _manager: DialogManager,
    error_: ValueError,
) -> None:
    """Notify user when the entered e-mail is invalid."""
    await message.answer(str(error_))


# Success handlers

async def on_start_registration(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """Start the registration process by moving to name input."""
    await callback.answer()
    await dialog_manager.next()


async def on_name_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Persist the entered name and go to the next step."""
    dialog_manager.dialog_data["reg_name"] = value
    await dialog_manager.next()


async def on_university_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Persist the university/education info and proceed."""
    dialog_manager.dialog_data["reg_university"] = value
    await dialog_manager.next()


async def on_email_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Persist the email, save to database, and complete registration."""
    dialog_manager.dialog_data["reg_email"] = value
    
    # Save registration data to database
    await save_registration_data(dialog_manager)
    
    # Transition to guest menu with stack reset
    await dialog_manager.start(
        state=GuestMenuSG.MAIN,
        mode=StartMode.RESET_STACK,
    )


# Database save functions

async def save_registration_data(dialog_manager: DialogManager) -> None:
    """
    Save registration data to users_info table.
    
    This function persists the collected registration information
    (name, education, email) to the database. In the future, this
    might be extended to include additional fields or tables.
    """
    db: DB | None = dialog_manager.middleware_data.get("db")
    user = dialog_manager.event.from_user
    
    if not db or not user:
        logger.warning("[REGISTRATION] Missing db or user")
        return
    
    try:
        # Get existing record to preserve other fields
        existing = await db.users_info.get_user_info(user_id=user.id)
        
        model = UsersInfoModel(
            user_id=user.id,
            full_name=dialog_manager.dialog_data.get("reg_name", ""),
            education=dialog_manager.dialog_data.get("reg_university", ""),
            email=dialog_manager.dialog_data.get("reg_email", ""),
            # Preserve existing fields if record exists
            username=existing.username if existing else user.username,
            university_course=existing.university_course if existing else None,
            occupation=existing.occupation if existing else None,
        )
        
        await db.users_info.upsert(model=model)
        await db.session.commit()
        logger.info("[REGISTRATION] Saved registration for user=%d", user.id)
        
    except Exception:
        logger.exception("[REGISTRATION] Failed to save registration data")
        if db:
            await db.session.rollback()


async def on_interview_button_clicked(
    callback: CallbackQuery,
    _button: Button,
    _dialog_manager: DialogManager,
) -> None:
    """Show a short alert explaining that interview booking is closed."""
    await callback.answer("Запись на интервью закрыта", show_alert=True)
