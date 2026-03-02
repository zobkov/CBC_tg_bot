"""Callback handlers for the grants dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from app.bot.assets.media_groups.media_groups import build_grants_course_media_group
from app.bot.dialogs.grants.states import GrantsSG

logger = logging.getLogger(__name__)


async def on_course_general_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Send course media group and navigate to COURSE window (general branch)."""
    media_group = build_grants_course_media_group()
    if media_group:
        try:
            await callback.bot.send_media_group(
                chat_id=callback.message.chat.id,
                media=media_group,
            )
        except Exception as e:
            logger.error("Failed to send grants course media group: %s", e)
    await dialog_manager.switch_to(GrantsSG.COURSE)


async def on_course_gsom_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Send course media group and navigate to COURSE_GSOM window."""
    media_group = build_grants_course_media_group()
    if media_group:
        try:
            await callback.bot.send_media_group(
                chat_id=callback.message.chat.id,
                media=media_group,
            )
        except Exception as e:
            logger.error("Failed to send grants course media group: %s", e)
    await dialog_manager.switch_to(GrantsSG.COURSE_GSOM)


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
