"""Handlers for the volunteer review dialog."""

import logging
from typing import Any

from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select

from .states import VolReviewSG

logger = logging.getLogger(__name__)


async def on_sync_to_sheets(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Trigger manual sync of part2 applications to Google Sheets."""
    await callback.answer("⏳ Синхронизирую...")

    db = manager.middleware_data.get("db")
    if not db:
        await callback.message.answer("❌ Ошибка доступа к базе данных")
        return

    try:
        from app.services.volunteer_part2_google_sync import VolunteerPart2GoogleSheetsSync

        sync_service = VolunteerPart2GoogleSheetsSync(db)
        count = await sync_service.sync_all_applications()
        await callback.message.answer(
            f"✅ Синхронизировано {count} заявок (этап 2) в Google Sheets"
        )
    except Exception as exc:
        logger.error("[VOL_REVIEW] on_sync_to_sheets failed: %s", exc)
        await callback.message.answer(f"❌ Ошибка синхронизации: {exc}")


async def on_page_selected(
    callback: CallbackQuery,
    _widget: Select,
    manager: DialogManager,
    item_id: str,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    manager.dialog_data["current_page"] = int(item_id)
    await manager.switch_to(VolReviewSG.PAGE)


async def on_app_selected(
    callback: CallbackQuery,
    _widget: Select,
    manager: DialogManager,
    item_id: str,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    manager.dialog_data["selected_user_id"] = int(item_id)
    await manager.switch_to(VolReviewSG.APP_DETAIL)


async def on_prev_page(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    current = manager.dialog_data.get("current_page", 0)
    manager.dialog_data["current_page"] = max(0, current - 1)
    await manager.switch_to(VolReviewSG.PAGE)


async def on_next_page(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    current = manager.dialog_data.get("current_page", 0)
    manager.dialog_data["current_page"] = current + 1
    await manager.switch_to(VolReviewSG.PAGE)


async def on_back_to_pages(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await manager.switch_to(VolReviewSG.PAGE_SELECT)


async def on_back_to_page(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Go back from APP_DETAIL to the page list."""
    await callback.answer()
    await manager.switch_to(VolReviewSG.PAGE)


async def on_toggle_reviewed(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Toggle the reviewed flag for the selected application."""
    await callback.answer()

    db = manager.middleware_data.get("db")
    selected_user_id: int | None = manager.dialog_data.get("selected_user_id")
    if not db or selected_user_id is None:
        return

    try:
        app = await db.volunteer_selection_part2.get(user_id=selected_user_id)
        if app is None:
            return
        new_value = not app.reviewed
        await db.volunteer_selection_part2.set_reviewed(
            user_id=selected_user_id, reviewed=new_value
        )
        await manager.switch_to(VolReviewSG.APP_DETAIL)
    except Exception as exc:
        logger.error("[VOL_REVIEW] on_toggle_reviewed failed: %s", exc)
        await callback.message.answer(f"❌ Ошибка: {exc}")


async def on_to_videos(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Send all 3 video notes and store their message IDs."""
    await callback.answer()

    bot: Bot = manager.middleware_data["bot"]
    chat_id = callback.message.chat.id

    db = manager.middleware_data.get("db")
    selected_user_id: int | None = manager.dialog_data.get("selected_user_id")

    if not db or selected_user_id is None:
        await callback.message.answer("❌ Нет данных для отображения видео.")
        return

    try:
        app = await db.volunteer_selection_part2.get(user_id=selected_user_id)
    except Exception as exc:
        logger.error("[VOL_REVIEW] on_to_videos: DB error: %s", exc)
        await callback.message.answer("❌ Ошибка БД при загрузке видео.")
        return

    if not app:
        await callback.message.answer("❌ Заявка не найдена.")
        return

    sent_ids: list[int] = []
    video_file_ids = [
        ("Видео-интервью 1/3", app.vq1_file_id),
        ("Видео-интервью 2/3", app.vq2_file_id),
        ("Видео-интервью 3/3", app.vq3_file_id),
    ]

    for label, file_id in video_file_ids:
        if not file_id:
            msg = await bot.send_message(chat_id, f"⚠️ {label}: файл отсутствует")
            sent_ids.append(msg.message_id)
            continue
        try:
            # Send label first, then the video note
            label_msg = await bot.send_message(chat_id, f"<b>{label}</b>")
            sent_ids.append(label_msg.message_id)
            video_msg = await bot.send_video_note(chat_id, file_id)
            sent_ids.append(video_msg.message_id)
        except Exception as exc:
            logger.error("[VOL_REVIEW] Failed to send video note %s: %s", label, exc)
            err_msg = await bot.send_message(chat_id, f"❌ {label}: ошибка отправки")
            sent_ids.append(err_msg.message_id)

    manager.dialog_data["video_msg_ids"] = sent_ids
    await manager.switch_to(VolReviewSG.VIDEO)


async def on_video_back(
    callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Delete the previously sent video messages and go back to APP_DETAIL."""
    await callback.answer()

    bot: Bot = manager.middleware_data["bot"]
    chat_id = callback.message.chat.id

    sent_ids: list[int] = manager.dialog_data.pop("video_msg_ids", [])
    for msg_id in sent_ids:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception as exc:
            logger.warning("[VOL_REVIEW] Could not delete msg %d: %s", msg_id, exc)

    await manager.switch_to(VolReviewSG.APP_DETAIL)
