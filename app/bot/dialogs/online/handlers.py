"""Callback handlers для онлайн-лекций"""

from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager

import logging

from app.infrastructure.database.database.db import DB
from app.bot.dialogs.online.states import OnlineSG

logger = logging.getLogger(__name__)


async def on_event_selected(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    item_id: str
) -> None:
    """Обработчик выбора лекции из расписания"""
    logger.debug("Selected event: %s", item_id)
    
    # Сохраняем slug выбранного события
    dialog_manager.dialog_data["selected_event_slug"] = item_id
    
    # Переходим к детальной информации
    await dialog_manager.switch_to(OnlineSG.SCHEDULE_EVENT)


async def on_my_event_selected(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    item_id: str
) -> None:
    """Обработчик выбора лекции из 'Моих лекций'"""
    logger.debug("Selected my event: %s", item_id)
    
    # Сохраняем slug выбранного события
    dialog_manager.dialog_data["selected_my_event_slug"] = item_id
    
    # Переходим к детальной информации
    await dialog_manager.switch_to(OnlineSG.MY_EVENT_DETAIL)


async def on_register_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager
) -> None:
    """Обработчик регистрации на лекцию"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None
    event_id = dialog_manager.dialog_data.get("selected_event_id")
    
    if not db or not user or not event_id:
        await callback.answer("Ошибка регистрации", show_alert=True)
        return
    
    try:
        # Регистрируем пользователя
        await db.online_registrations.register(user_id=user.id, event_id=event_id)
        await db.session.flush()
        
        # Получаем название лекции для сообщения об успехе
        event_obj = await db.online_events.get_by_id(id=event_id)
        if event_obj:
            dialog_manager.dialog_data["registered_event_title"] = event_obj.title
        
        logger.info("User %s registered for event %s", user.id, event_id)
        
        # Переходим к экрану успешной регистрации
        await dialog_manager.switch_to(OnlineSG.SUCCESSFUL_REGISTRATION)
        
    except Exception as e:
        logger.error("Error registering user: %s", e)
        await callback.answer("Ошибка при регистрации. Попробуйте позже.", show_alert=True)


async def on_cancel_registration_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager
) -> None:
    """Обработчик отмены регистрации на лекцию"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None
    event_id = dialog_manager.dialog_data.get("selected_event_id")
    
    if not db or not user or not event_id:
        await callback.answer("Ошибка отмены регистрации", show_alert=True)
        return
    
    try:
        # Отменяем регистрацию
        await db.online_registrations.cancel(user_id=user.id, event_id=event_id)
        await db.session.flush()
        
        logger.info("User %s cancelled registration for event %s", user.id, event_id)
        
        await callback.answer("Регистрация отменена", show_alert=False)
        
        # Возвращаемся к расписанию
        await dialog_manager.switch_to(OnlineSG.SCHEDULE)
        
    except Exception as e:
        logger.error("Error cancelling registration: %s", e)
        await callback.answer("Ошибка при отмене регистрации. Попробуйте позже.", show_alert=True)


async def on_get_link_clicked(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager
) -> None:
    """Обработчик получения ссылки на трансляцию"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event_id = dialog_manager.dialog_data.get("selected_event_id")
    
    if not db or not event_id:
        await callback.answer("Ошибка получения ссылки", show_alert=True)
        return
    
    try:
        # Получаем событие
        event_obj = await db.online_events.get_by_id(id=event_id)
        
        if not event_obj:
            await callback.answer("Лекция не найдена", show_alert=True)
            return
        
        # Проверяем доступность ссылки (должна быть доступна за 1 час до начала)
        from app.utils.datetime_formatters import is_link_available, format_moscow_datetime
        
        if not is_link_available(event_obj.start_at, hours_before=1):
            available_time = format_moscow_datetime(event_obj.start_at, include_tz=False)
            await callback.answer(
                f"Ссылка будет доступна {available_time} (МСК)",
                show_alert=True
            )
            return
        
        if not event_obj.url:
            await callback.answer("Ссылка пока не добавлена", show_alert=True)
            return
        
        # Отправляем ссылку отдельным сообщением
        await callback.message.answer(
            f"🔗 Ссылка на трансляцию:\n{event_obj.url}",
            disable_web_page_preview=False
        )
        
        await callback.answer("Ссылка отправлена!", show_alert=False)
        
    except Exception as e:
        logger.error("Error getting link: %s", e)
        await callback.answer("Ошибка при получении ссылки. Попробуйте позже.", show_alert=True)
