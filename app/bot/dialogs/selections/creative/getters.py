"""Dialog data getters for the creative selection (casting) dialog."""

import logging
from typing import Any

from aiogram_dialog import DialogManager

logger = logging.getLogger(__name__)


async def get_directions(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Provide direction options for selection."""
    return {
        "directions": [
            {"id": "ceremony", "text": "Церемония открытия (в роли актёра)"},
            {"id": "fair", "text": "Ярмарка культуры (проведение мастер-классов и интерактивов)"},
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
            {"id": "wheel", "text": "Интерактив: Колесо удачи"},
            {"id": "dragon_race", "text": "Интерактив: Гонки драконов (мини-версия Dragon Boat)"},
            {"id": "sachet", "text": "Интерактив: сбор аромасаше"},
            {"id": "fortune", "text": "Интерактив: Китайское гадание (по книге перемен И Цзин и монетам)"},
            {"id": "embroidery", "text": "МК: Вышивка небольших рисунков в китайской стилистике"},
            {"id": "wind_music", "text": "МК: Создание подвески «Музыка ветра»"},
            {"id": "amulets", "text": "МК: Создание металлических амулетов с отчеканенными символами"},
            {"id": "mask_painting", "text": "МК: Роспись масок из Пекинской оперы"},
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
        "direction": "Церемония открытия" if direction == "ceremony" else "Ярмарка культуры",
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
