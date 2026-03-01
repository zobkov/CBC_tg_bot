"""Callback handlers for the grants dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from app.bot.dialogs.grants.states import GrantsSG

logger = logging.getLogger(__name__)


async def on_lesson_selected(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    """Store the selected lesson tag and navigate to the LESSON window."""
    logger.debug("Lesson selected: tag=%s, user=%d", item_id, callback.from_user.id)
    dialog_manager.dialog_data["selected_lesson_tag"] = item_id
    await dialog_manager.switch_to(GrantsSG.LESSON)
