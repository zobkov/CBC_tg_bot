"""Handlers, validators, and helpers for the creative selection (casting) dialog."""

import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Multiselect, Radio

from .states import CreativeSelectionSG

logger = logging.getLogger(__name__)


# Input validators / type factories

def name_check(value: str) -> str:
    """Validate and sanitize the applicant's name."""
    name = value.strip()

    if not name:
        raise ValueError("Имя не может быть пустым")
    if len(name) < 2:
        raise ValueError("Имя должно содержать минимум 2 символа")

    return name


# Error handlers

async def on_name_error(
    message: Message,
    _dialog: Any,
    _manager: DialogManager,
    error_: ValueError,
) -> None:
    """Notify user when the entered name is invalid."""
    await message.answer(str(error_))


# Navigation handlers

async def on_start_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Start the application flow and clear any previous data."""
    await callback.answer()
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(CreativeSelectionSG.name)


async def on_go_home(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Return to main menu by closing the dialog."""
    await callback.answer()
    await dialog_manager.done()


# Common input handlers

async def on_name_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store name and proceed to next step."""
    dialog_manager.dialog_data["creative_name"] = value
    await dialog_manager.next()


async def on_contact_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store contact info and proceed."""
    dialog_manager.dialog_data["creative_contact"] = value.strip()
    await dialog_manager.next()


async def on_email_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store email and proceed."""
    dialog_manager.dialog_data["creative_email"] = value.strip()
    await dialog_manager.next()


async def on_university_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store university info and proceed."""
    dialog_manager.dialog_data["creative_university"] = value.strip()
    await dialog_manager.next()


# Direction selection (branch point)

async def on_direction_selected(
    callback: CallbackQuery,
    _widget: Radio,
    dialog_manager: DialogManager,
    item_id: str,
    **_kwargs: Any,
) -> None:
    """Store direction and route to appropriate branch."""
    await callback.answer()
    dialog_manager.dialog_data["creative_direction"] = item_id

    # Route to appropriate branch
    if item_id == "ceremony":
        await dialog_manager.switch_to(CreativeSelectionSG.ceremony_stage_experience)
    elif item_id == "fair":
        await dialog_manager.switch_to(CreativeSelectionSG.fair_role_selection)
    else:
        logger.warning("[CREATIVE] Unknown direction: %s", item_id)
        await callback.message.answer("Произошла ошибка. Попробуйте еще раз.")


# Ceremony branch handlers

async def on_ceremony_stage_exp_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store ceremony stage experience."""
    dialog_manager.dialog_data["ceremony_stage_experience"] = value.strip()
    await dialog_manager.next()


async def on_ceremony_motivation_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store ceremony motivation."""
    dialog_manager.dialog_data["ceremony_motivation"] = value.strip()
    await dialog_manager.next()


async def on_rehearsal_attendance_selected(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Store rehearsal attendance choice and proceed."""
    await callback.answer()
    # Check button ID to determine if user can attend
    can_attend = "can_attend" in callback.data
    dialog_manager.dialog_data["ceremony_can_attend_md"] = can_attend
    await dialog_manager.next()


async def on_frequency_selected(
    callback: CallbackQuery,
    _widget: Radio,
    dialog_manager: DialogManager,
    item_id: str,
    ** _kwargs: Any,
) -> None:
    """Store rehearsal frequency and proceed."""
    await callback.answer()
    dialog_manager.dialog_data["ceremony_rehearsal_frequency"] = item_id
    await dialog_manager.next()


async def on_duration_selected(
    callback: CallbackQuery,
    _widget: Radio,
    dialog_manager: DialogManager,
    item_id: str,
    **_kwargs: Any,
) -> None:
    """Store rehearsal duration and proceed."""
    await callback.answer()
    dialog_manager.dialog_data["ceremony_rehearsal_duration"] = item_id
    await dialog_manager.next()


async def on_timeslots_changed(
    _event: Any,
    _multiselect: Multiselect,
    _manager: DialogManager,
    _item_id: str,
    **_kwargs: Any,
) -> None:
    """Track timeslot selection changes (called automatically)."""
    # Selections are automatically tracked in dialog_data by widget ID
    pass


async def on_timeslots_confirmed(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Store selected timeslots and proceed."""
    await callback.answer()
    # Get selected items from widget state
    widget_id = "timeslots_multiselect"
    selected = dialog_manager.dialog_data.get(widget_id, [])
    dialog_manager.dialog_data["ceremony_timeslots"] = selected
    await dialog_manager.next()


async def on_ceremony_cloud_link_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store cloud link and proceed to confirmation."""
    dialog_manager.dialog_data["ceremony_cloud_link"] = value.strip()
    await dialog_manager.switch_to(CreativeSelectionSG.confirmation)


async def on_skip_ceremony_cloud(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Skip cloud link and proceed to confirmation."""
    await callback.answer()
    dialog_manager.dialog_data["ceremony_cloud_link"] = None
    await dialog_manager.switch_to(CreativeSelectionSG.confirmation)


# Fair branch handlers

async def on_fair_roles_changed(
    _event: Any,
    _multiselect: Multiselect,
    _manager: DialogManager,
    _item_id: str,
    **_kwargs: Any,
) -> None:
    """Track fair role selection changes (called automatically)."""
    # Selections are automatically tracked in dialog_data by widget ID
    pass


async def on_fair_roles_confirmed(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Store selected fair roles and proceed."""
    await callback.answer()
    # Get selected items from widget state
    widget_id = "fair_roles_multiselect"
    selected = dialog_manager.dialog_data.get(widget_id, [])
    dialog_manager.dialog_data["fair_roles"] = selected
    await dialog_manager.next()


async def on_fair_motivation_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store fair motivation."""
    dialog_manager.dialog_data["fair_motivation"] = value.strip()
    await dialog_manager.next()


async def on_fair_experience_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store fair experience."""
    dialog_manager.dialog_data["fair_experience"] = value.strip()
    await dialog_manager.next()


async def on_fair_cloud_link_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Store cloud link and proceed to confirmation."""
    dialog_manager.dialog_data["fair_cloud_link"] = value.strip()
    await dialog_manager.switch_to(CreativeSelectionSG.confirmation)


async def on_skip_fair_cloud(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Skip cloud link and proceed to confirmation."""
    await callback.answer()
    dialog_manager.dialog_data["fair_cloud_link"] = None
    await dialog_manager.switch_to(CreativeSelectionSG.confirmation)


# Submission handlers

async def on_submit_application(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Submit application to database and Google Sheets."""
    await callback.answer()

    user = callback.from_user
    if not user:
        await callback.message.answer("Ошибка: не удалось определить пользователя")
        return

    # Send confirmation to user first
    await callback.message.answer(
        "✅ Спасибо! Твоя заявка принята.\n\n"
        "Мы свяжемся с тобой в бл ижайшее время!"
    )

    # Call placeholder functions
    await save_to_database(dialog_manager, user.id)
    await sync_to_google_sheets(dialog_manager, user.id)

    await dialog_manager.switch_to(CreativeSelectionSG.success)


# Placeholder functions for future implementation

async def save_to_database(manager: DialogManager, user_id: int) -> None:
    """
    Placeholder: Save creative selection application to database.

    TODO: Create database table 'creative_applications' with columns:
    - user_id (int, primary key)
    - name (text)
    - contact (text)
    - email (text)
    - university (text)
    - direction (text: 'ceremony' or 'fair')
    - ceremony_stage_experience (text, nullable)
    - ceremony_motivation (text, nullable)
    - ceremony_can_attend_md (boolean, nullable)
    - ceremony_rehearsal_frequency (text, nullable)
    - ceremony_rehearsal_duration (text, nullable)
    - ceremony_timeslots (jsonb, nullable)
    - ceremony_cloud_link (text, nullable)
    - fair_roles (jsonb, nullable)
    - fair_motivation (text, nullable)
    - fair_experience (text, nullable)
    - fair_cloud_link (text, nullable)
    - submitted_at (timestamp)

    TODO: Create database class similar to _QuizDodUsersInfoDB
    TODO: Add to DB class in /app/infrastructure/database/database/db.py
    """
    logger.info("[CREATIVE] Would save application for user=%s with data: %s",
                user_id, manager.dialog_data)


async def sync_to_google_sheets(manager: DialogManager, user_id: int) -> None:
    """
    Placeholder: Sync creative application to Google Sheets.

    TODO: Create Google Sheet with tabs:
    - "Церемония открытия" (Ceremony applications)
    - "Ярмарка культуры" (Fair applications)

    TODO: Integrate with GoogleSyncService similar to interview sync
    TODO: Map dialog_data fields to spreadsheet columns
    """
    logger.info("[CREATIVE] Would sync to Google Sheets for user=%s with data: %s",
                user_id, manager.dialog_data)
