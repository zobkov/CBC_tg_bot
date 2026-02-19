"""
Data getters для онлайн-лекций
"""

import logging
from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.online_events import OnlineEventModel
from app.utils.datetime_formatters import format_moscow_datetime, format_date_only, format_date_short, format_time_only, is_link_available

logger = logging.getLogger(__name__)


async def get_schedule_list(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Получить список предстоящих лекций для расписания"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None
    
    if not db:
        return {"schedule_text": "Ошибка загрузки расписания", "events": []}
    
    try:
        # Получаем активные предстоящие лекции (скрываем те, что начались >3 часов назад)
        events: list[OnlineEventModel] = await db.online_events.list_active_upcoming(hide_older_than_hours=3)
        
        if not events:
            return {
                "schedule_text": "На данный момент нет запланированных лекций. Следите за обновлениями! 📚",
                "events": []
            }
        
        # Получаем регистрации пользователя, если он авторизован
        user_registrations = set()
        if user:
            registrations = await db.online_registrations.get_user_registrations(
                user_id=user.id,
                active_only=True
            )
            user_registrations = {reg.event_id for reg in registrations}
        
        # Формируем текст расписания
        schedule_text = ""
        for event in events:
            date_str = format_date_only(event.start_at)
            time_str = format_time_only(event.start_at)
            # Добавляем ✅ если пользователь зарегистрирован
            status_emoji = " ✅" if event.id in user_registrations else ""
            
            schedule_text += f"📝 {event.title}\n"
            if event.speaker:
                schedule_text += f"🎙️ {event.speaker}\n"
            schedule_text += f"\n📅 {date_str}, {time_str} (МСК){status_emoji}\n\n\n"
        
        # Формируем список для кнопок в формате "DD.MM – alias"
        events_list = [(f"{format_date_short(e.start_at)} – {e.alias}", e.slug) for e in events]
        
        return {
            "schedule_text": schedule_text.strip(),
            "events": events_list
        }
    except Exception as e:
        logger.error("Error loading schedule: %s", e)
        return {"schedule_text": "Ошибка загрузки расписания", "events": []}


async def get_event_details(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Получить детальную информацию о лекции"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event_slug = dialog_manager.dialog_data.get("selected_event_slug")
    
    if not db or not event_slug:
        return {"event_details": "Ошибка загрузки информации о лекции"}
    
    try:
        event: OnlineEventModel | None = await db.online_events.get_by_slug(slug=event_slug)
        
        if not event:
            return {"event_details": "Лекция не найдена"}
        
        # Проверяем статус регистрации
        event_obj = getattr(dialog_manager, "event", None)
        user = getattr(event_obj, "from_user", None) if event_obj else None
        
        registration_status = ""
        is_registered = False
        
        if user:
            status = await db.online_registrations.check_registration_status(
                user_id=user.id,
                event_id=event.id
            )
            if status == "active":
                registration_status = "\n✅ Ты зарегистрирован на эту лекцию"
                is_registered = True
        
        # Формируем детальную информацию
        details = f"Лекция: <b>{event.title}</b>\n"
        if event.speaker:
            details += f"Спикер: <b>{event.speaker}</b>\n"
        details += f"\nДата и время: {format_moscow_datetime(event.start_at)}\n\n"
        
        if event.description:
            details += f"Описание:\n{event.description}\n\n"
        
        # Показываем ссылку только если до начала осталось меньше часа
        if event.url and is_link_available(event.start_at, hours_before=1):
            details += f"Ссылка на лекцию:\n🔗 {event.url}\n\n"
        
        details += registration_status
        
        # Сохраняем event_id для обработчиков
        dialog_manager.dialog_data["selected_event_id"] = event.id
        
        return {
            "event_details": details,
            "event_title": event.title,
            "event_id": event.id,
            "is_registered": is_registered,
            "link_available": is_link_available(event.start_at, hours_before=1),
            "event_url": event.url or "",
        }
    except Exception as e:
        logger.error("Error loading event details: %s", e)
        return {"event_details": "Ошибка загрузки информации о лекции"}


async def get_my_events(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Получить список лекций, на которые зарегистрирован пользователь"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None
    
    if not db or not user:
        return {"my_events_text": "Ошибка загрузки списка лекций", "my_events": []}
    
    try:
        # Получаем регистрации с деталями событий
        registrations = await db.online_registrations.get_registration_with_event_details(user_id=user.id)
        
        if not registrations:
            return {
                "my_events_text": "У тебя пока нет зарегистрированных лекций.\n\nПросмотри расписание и зарегистрируйся на интересующие тебя мероприятия! 📚",
                "my_events": []
            }
        
        # Формируем текст списка
        my_events_text = ""
        for reg in registrations:
            date_str = format_date_only(reg["start_at"])
            time_str = format_time_only(reg["start_at"])
            my_events_text += f"📝 {reg['title']}\n"
            if reg["speaker"]:
                my_events_text += f"🎙️ {reg['speaker']}\n"
            my_events_text += f"\n📅 {date_str}, {time_str} (МСК)\n\n\n"
        
        # Формируем список для кнопок в формате "DD.MM – alias"
        events_list = [(f"{format_date_short(r['start_at'])} – {r['alias']}", r['slug']) for r in registrations]
        
        return {
            "my_events_text": my_events_text.strip(),
            "my_events": events_list
        }
    except Exception as e:
        logger.error("Error loading user events: %s", e)
        return {"my_events_text": "Ошибка загрузки списка лекций", "my_events": []}


async def get_my_event_detail(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Получить детальную информацию о лекции из 'Моих лекций'"""
    db: DB | None = dialog_manager.middleware_data.get("db")
    event_slug = dialog_manager.dialog_data.get("selected_my_event_slug")
    
    if not db or not event_slug:
        return {"my_event_details": "Ошибка загрузки информации о лекции"}
    
    try:
        event: OnlineEventModel | None = await db.online_events.get_by_slug(slug=event_slug)
        
        if not event:
            return {"my_event_details": "Лекция не найдена"}
        
        # Формируем детальную информацию
        details = f"Лекция: <b>{event.title}</b>\n"
        if event.speaker:
            details += f"Спикер: <b>{event.speaker}</b>\n"
        details += f"\nДата и время: {format_moscow_datetime(event.start_at)}\n\n"
        
        if event.description:
            details += f"Описание:\n{event.description}\n\n"
        
        # Статус ссылки
        link_avail = is_link_available(event.start_at, hours_before=1)
        if link_avail and event.url:
            details += f"🎥 Ссылка активна: {event.url}\n\n"
        else:
            # Показываем когда будет доступна
            available_time = format_moscow_datetime(event.start_at, include_tz=False)
            details += f"🔗 Ссылка будет доступна {available_time} (МСК)\n\n"
        
        # Сохраняем event_id для обработчиков
        dialog_manager.dialog_data["selected_event_id"] = event.id
        
        return {
            "my_event_details": details,
            "event_title": event.title,
            "event_id": event.id,
            "link_available": link_avail,
            "event_url": event.url or "",
        }
    except Exception as e:
        logger.error("Error loading my event details: %s", e)
        return {"my_event_details": "Ошибка загрузки информации о лекции"}


async def get_successful_registration_text(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Получить текст успешной регистрации"""
    event_title = dialog_manager.dialog_data.get("registered_event_title", "лекцию")
    
    text = f"""Поздравляем! Ты успешно зарегистрирован на лекцию <b>{event_title}</b> 🎉

Ссылка на трансляцию станет активна в карточке мероприятия за 1 час до начала мероприятия. Мы также пришлем тебе напоминание 🔔

Твои зарегистрированные лекции всегда можно найти в разделе «📚 Мои лекции»"""
    
    return {"success_text": text}


async def get_ics_file(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Получить ICS файл для добавления в календарь"""
    from aiogram_dialog.api.entities import MediaAttachment, MediaId
    from aiogram.enums import ContentType
    from app.utils.ics_file_id import get_ics_file_id
    
    # Получаем slug выбранного события
    event_slug = dialog_manager.dialog_data.get("selected_event_slug")
    
    if not event_slug:
        logger.warning("No event_slug found for ICS file getter")
        return {}
    
    # Получаем file_id для ICS файла
    file_id = get_ics_file_id(event_slug)
    
    if not file_id:
        logger.warning(f"No file_id found for ICS file with slug: {event_slug}")
        return {}
    
    # Создаем MediaAttachment для DynamicMedia
    ics_media = MediaAttachment(
        ContentType.DOCUMENT,
        file_id=MediaId(file_id)
    )
    
    return {"ics_file": ics_media}
