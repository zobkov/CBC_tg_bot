"""Handlers for settings dialog."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from better_profanity import profanity

from app.bot.dialogs.guest.quiz_dod.profanity_list import RUSSIAN_PROFANITY
from app.bot.dialogs.settings.states import SettingsSG
from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.user_info import UsersInfoModel

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


def education_check(value: str) -> str:
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


async def education_error_handler(
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

async def on_name_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Save the new name and update database."""
    await _update_user_field(dialog_manager, "full_name", value)
    await _message.answer("✅ Имя обновлено!")
    await dialog_manager.switch_to(SettingsSG.PROFILE)


async def on_education_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Save the new education info and update database."""
    await _update_user_field(dialog_manager, "education", value)
    await _message.answer("✅ Информация об обучении обновлена!")
    await dialog_manager.switch_to(SettingsSG.PROFILE)


async def on_email_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Save the new email and update database."""
    await _update_user_field(dialog_manager, "email", value)
    await _message.answer("✅ Email обновлен!")
    await dialog_manager.switch_to(SettingsSG.PROFILE)


# Helper functions

async def _update_user_field(
    dialog_manager: DialogManager,
    field_name: str,
    value: str,
) -> None:
    """Update a specific field in user_info table."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    user = dialog_manager.event.from_user
    
    if not db or not user:
        logger.warning(f"[SETTINGS] Missing db or user for field update: {field_name}")
        return
    
    try:
        # Get existing record
        existing = await db.users_info.get_user_info(user_id=user.id)
        
        # Prepare updated model
        model_data = {
            "user_id": user.id,
            "full_name": existing.full_name if existing else None,
            "education": existing.education if existing else None,
            "email": existing.email if existing else None,
            "username": existing.username if existing else user.username,
            "university_course": existing.university_course if existing else None,
            "occupation": existing.occupation if existing else None,
        }
        
        # Update the specific field
        model_data[field_name] = value
        
        model = UsersInfoModel(**model_data)
        
        await db.users_info.upsert(model=model)
        await db.session.commit()
        logger.info(f"[SETTINGS] Updated {field_name} for user={user.id}")
        
    except Exception:
        logger.exception(f"[SETTINGS] Failed to update {field_name}")
        if db:
            await db.session.rollback()
