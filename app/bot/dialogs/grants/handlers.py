"""Callback handlers for the grants dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from app.bot.assets.media_groups.media_groups import build_grants_course_media_group
from app.bot.dialogs.grants.states import GrantsSG

logger = logging.getLogger(__name__)


async def _send_course_media_group(callback: CallbackQuery, dialog_manager: DialogManager) -> None:
    """Send course media group and persist message IDs for later deletion."""
    media_group = build_grants_course_media_group()
    if media_group:
        try:
            sent_messages = await callback.bot.send_media_group(
                chat_id=callback.message.chat.id,
                media=media_group,
            )
            dialog_manager.dialog_data["course_media_group_ids"] = [
                msg.message_id for msg in sent_messages
            ]
        except Exception as e:
            logger.error("Failed to send grants course media group: %s", e)


async def _delete_course_media_group(callback: CallbackQuery, dialog_manager: DialogManager) -> None:
    """Delete previously sent course media group messages."""
    message_ids = dialog_manager.dialog_data.pop("course_media_group_ids", None)
    if message_ids:
        try:
            for message_id in message_ids:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=message_id,
                )
        except Exception as e:
            logger.error("Failed to delete grants course media group: %s", e)


async def on_course_general_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Send course media group and navigate to COURSE window (general branch)."""
    await _send_course_media_group(callback, dialog_manager)
    await dialog_manager.switch_to(GrantsSG.COURSE)


async def on_course_gsom_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Send course media group and navigate to COURSE_GSOM window."""
    await _send_course_media_group(callback, dialog_manager)
    await dialog_manager.switch_to(GrantsSG.COURSE_GSOM)


async def on_back_from_course(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Delete course media group and go back to MAIN_GENERAL."""
    await _delete_course_media_group(callback, dialog_manager)
    await dialog_manager.switch_to(GrantsSG.MAIN_GENERAL)


async def on_back_from_course_gsom(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Delete course media group and go back to MAIN_GSOM."""
    await _delete_course_media_group(callback, dialog_manager)
    await dialog_manager.switch_to(GrantsSG.MAIN_GSOM)


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
