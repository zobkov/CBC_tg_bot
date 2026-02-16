"""Dialog data getters for the creative selection (casting) dialog."""

import logging
from typing import Any

from aiogram_dialog import DialogManager
from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from app.utils.optimized_dialog_widgets import get_file_id_for_path

logger = logging.getLogger(__name__)


async def get_creative_intro_media(**_kwargs: Any) -> dict[str, Any]:
    """Load photo attachment definition for the creative selection intro."""
    relative_path = "creative_casting/creative_selection.png"
    file_id = get_file_id_for_path(relative_path)

    if file_id:
        media = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path=f"app/bot/assets/images/{relative_path}",
        )

    return {"media": media}


async def get_main_text(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide main intro text based on whether user has existing application."""
    from app.infrastructure.database.database.db import DB

    # Get database instance
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = dialog_manager.event
    user_id = event.from_user.id if event and event.from_user else None

    has_application = False
    existing_direction = None

    # Check if user has existing application
    if db and user_id:
        try:
            existing_app = await db.creative_applications.get_application(user_id=user_id)
            if existing_app:
                has_application = True
                existing_direction = existing_app.direction
                logger.info(
                    "[CREATIVE] User %d has existing application: direction=%s",
                    user_id,
                    existing_direction,
                )
        except Exception as e:
            logger.error(
                "[CREATIVE] Failed to check existing application for user %d: %s",
                user_id,
                e,
            )

    # Return appropriate text
    if has_application:
        direction_text = (
            "церемонии открытия и закрытия"
            if existing_direction == "ceremony"
            else "ярмарки культуры"
        )
        intro_text = (
            "🎭 <b>Заявка на кастинг форума «Китай Бизнес Культура» 2026</b>\n\n"
            f"✅ <b>Ты уже подал заявку на «{direction_text}».</b>\n\n"
            "Если хочешь изменить данные, просто отправь заявку заново — она автоматически заменит предыдущую."
            "Ты можешь:\n"
            "• исправить все ответы\n"
            "• выбрать другое направление (например, мастер-классы вместо церемонии)\n"
            "• обновить контактную информацию\n\n"
            "Заполнение займет около 5-7 минут."
        )
    else:
        intro_text = (
            "🎭 <b>Заявка на кастинг форума «Китай Бизнес Культура» 2026</b>\n\n"
            "Добро пожаловать на кастинг для форума КБК!\n\n"
            "Тебе предстоит выбрать одно из направлений:\n"
            "• Церемония открытия и закрытия (в роли актёра)\n"
            "• Ярмарка культуры (проведение мастер-классов и интерактивов)\n\n"
            "Заполнение займет около 5-7 минут. Удачи!"
        )

    return {"intro_text": intro_text}


async def get_directions(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide direction options for selection."""
    return {
        "directions": [
            {"id": "ceremony", "text": "Церемония открытия и закрытия"},
            {"id": "fair", "text": "Ярмарка культуры"},
        ]
    }


async def get_frequency_options(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide rehearsal frequency options."""
    return {
        "frequency_options": [
            {"id": "once", "text": "1 раз"},
            {"id": "twice", "text": "2 раза"},
            {"id": "thrice", "text": "3 раза"},
            {"id": "as_needed", "text": "При необходимости, больше раз"},
        ]
    }


async def get_duration_options(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide rehearsal duration options."""
    return {
        "duration_options": [
            {"id": "up_to_1h", "text": "не больше 1 часа"},
            {"id": "1_2h", "text": "1-2 часа"},
            {"id": "2_3h", "text": "2-3 часа"},
        ]
    }


async def get_timeslot_options(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide timeslot options and track selections."""
    selected = dialog_manager.dialog_data.get("timeslots_multiselect", [])
    return {
        "timeslot_options": [
            {"id": "17:00", "text": "17:00"},
            {"id": "18:00", "text": "18:00"},
            {"id": "19:00", "text": "19:00"},
            {"id": "20:00", "text": "20:00"},
            {"id": "21:00", "text": "21:00"},
        ],
        "has_timeslots": len(selected) > 0,
    }


async def get_fair_role_options(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide fair role options and track selections."""
    selected = dialog_manager.dialog_data.get("fair_roles_multiselect", [])
    return {
        "fair_role_options": [
            {"id": "wheel", "text": "1 - Интерактив: Колесо удачи"},
            {"id": "dragon_race", "text": "2 - Интерактив: Гонки драконов "},
            {"id": "sachet", "text": "3 - Интерактив: сбор аромасаше"},
            {"id": "fortune", "text": "4 - Интерактив: Китайское гадание"},
            {"id": "embroidery", "text": "5 - МК: Вышивка небольших рисунков"},
            {"id": "wind_music", "text": "6 - МК: Создание подвески «Музыка ветра»"},
            {"id": "amulets", "text": "7 - МК: Создание металлических амулетов"},
            {"id": "mask_painting", "text": "8 - МК: Роспись масок из Пекинской оперы"},
        ],
        "has_fair_roles": len(selected) > 0,
    }


async def get_selected_fair_roles(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide selected fair roles for display in motivation window."""
    roles = dialog_manager.dialog_data.get("fair_roles", [])
    return {
        "selected_roles": _format_fair_roles(roles),
    }


async def get_confirmation_data(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Prepare confirmation summary with all collected data."""
    data = dialog_manager.dialog_data
    direction = data.get("creative_direction")

    # Format branch-specific details
    if direction == "ceremony":
        timeslots = data.get("ceremony_timeslots", [])
        timeslots_text = ", ".join(timeslots) if timeslots else "Не указано"

        branch_details = (
            f"<b>Опыт на сцене:</b> {data.get('ceremony_stage_experience', 'N/A')}\n\n"
            f"<b>Мотивация:</b> {data.get('ceremony_motivation', 'N/A')}\n\n"
            f"<b>Посещение МД:</b> {'Смогу' if data.get('ceremony_can_attend_md') else 'Не смогу'}\n\n"
            f"<b>Частота репетиций:</b> {_format_frequency(data.get('ceremony_rehearsal_frequency'))}\n\n"
            f"<b>Длительность:</b> {_format_duration(data.get('ceremony_rehearsal_duration'))}\n\n"
            f"<b>Временные слоты:</b> {timeslots_text}\n\n"
            f"<b>Материалы:</b> {data.get('ceremony_cloud_link') or 'Не указано'}"
        )
    else:  # fair
        roles = data.get("fair_roles", [])
        branch_details = (
            f"<b>Выбранные роли:</b>\n{_format_fair_roles(roles)}\n\n"
            f"<b>Почему выбрали:</b> {data.get('fair_motivation', 'N/A')}\n\n"
            f"<b>Опыт:</b> {data.get('fair_experience', 'N/A')}\n\n"
            f"<b>Материалы:</b> {data.get('fair_cloud_link') or 'Не указано'}"
        )

    return {
        "name": data.get("creative_name", "N/A"),
        "contact": data.get("creative_contact", "N/A"),
        "email": data.get("creative_email", "N/A"),
        "university": data.get("creative_university", "N/A"),
        "direction": "Церемония открытия и закрытия" if direction == "ceremony" else "Ярмарка культуры",
        "branch_details": branch_details,
    }


def _format_frequency(freq_id: str | None) -> str:
    """Format frequency ID to display text."""
    if not freq_id:
        return "N/A"
    mapping = {
        "once": "1 раз",
        "twice": "2 раза",
        "thrice": "3 раза",
        "as_needed": "При необходимости, больше раз",
    }
    return mapping.get(freq_id, freq_id)


def _format_duration(dur_id: str | None) -> str:
    """Format duration ID to display text."""
    if not dur_id:
        return "N/A"
    mapping = {
        "up_to_1h": "не больше 1 часа",
        "1_2h": "1-2 часа",
        "2_3h": "2-3 часа",
    }
    return mapping.get(dur_id, dur_id)


def _format_fair_roles(role_ids: list[str]) -> str:
    """Format fair role IDs to display text."""
    if not role_ids:
        return "Не указано"

    mapping = {
        "wheel": "Интерактив: Колесо удачи",
        "dragon_race": "Интерактив: Гонки драконов (мини-версия Dragon Boat)",
        "sachet": "Интерактив: сбор аромасаше",
        "fortune": "Интерактив: Китайское гадание (по книге перемен И Цзин и монетам)",
        "embroidery": "МК: Вышивка небольших рисунков в китайской стилистике",
        "wind_music": "МК: Создание подвески «Музыка ветра»",
        "amulets": "МК: Создание металлических амулетов с отчеканенными символами",
        "mask_painting": "МК: Роспись масок из Пекинской оперы",
    }
    return "\n".join([f"• {mapping.get(rid, rid)}" for rid in role_ids])
