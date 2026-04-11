"""Handlers for the lectory dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput

from app.infrastructure.database.database.db import DB

from .states import LectorySG

logger = logging.getLogger(__name__)

_MAX_QUESTION_LEN = 1000


async def on_event_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    """Store selected event key and navigate to event detail."""
    manager.dialog_data["selected_event"] = item_id
    manager.dialog_data.pop("question_submitted", None)
    await manager.switch_to(LectorySG.EVENT_DETAIL)


def question_validator(value: str) -> str:
    """Strip and validate question text length."""
    text = value.strip()
    if not text:
        raise ValueError("Вопрос не может быть пустым")
    if len(text) > _MAX_QUESTION_LEN:
        raise ValueError(f"Вопрос слишком длинный (максимум {_MAX_QUESTION_LEN} символов)")
    return text


async def on_question_submitted(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    value: str,
) -> None:
    """Save submitted question to DB and return to event detail."""
    event_key: str = manager.dialog_data.get("selected_event", "")
    event_name: str = manager.dialog_data.get("selected_event_name", "")

    db: DB | None = manager.middleware_data.get("db")
    if db and message.from_user:
        try:
            await db.lectory_questions.add_question(
                user_id=message.from_user.id,
                event_key=event_key,
                event_name=event_name,
                question_text=value,
            )
        except Exception as exc:
            logger.error("Failed to save lectory question: %s", exc)

    manager.dialog_data["question_submitted"] = True
    await manager.switch_to(LectorySG.EVENT_DETAIL)


async def on_question_error(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    error: ValueError,
) -> None:
    """Notify user about validation failure."""
    await message.answer(f"⚠️ {error}")
