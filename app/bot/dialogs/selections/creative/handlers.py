"""Handlers, validators, and helpers for the creative selection (casting) dialog."""

import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Multiselect, Radio
from aiogram_dialog import ShowMode

from app.bot.assets.media_groups.media_groups import build_creative_casting_media_group
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
        # Send photo gallery for fair roles
        media_group = build_creative_casting_media_group()
        if media_group:
            try:
                sent_messages = await callback.bot.send_media_group(
                    chat_id=callback.message.chat.id,
                    media=media_group
                )
                # Save message IDs for later deletion
                media_group_message_ids = [msg.message_id for msg in sent_messages]
                dialog_manager.dialog_data["media_group_message_ids"] = media_group_message_ids
            except Exception as e:
                logger.error("[CREATIVE] Failed to send media group: %s", e)

        await dialog_manager.switch_to(CreativeSelectionSG.fair_role_selection, show_mode=ShowMode.DELETE_AND_SEND)
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

    # Get selected items from Multiselect widget
    multiselect = dialog_manager.find("timeslots_multiselect")
    checked_items = []
    if multiselect:
        checked_items = list(multiselect.get_checked())
        logger.info("[CREATIVE] Selected timeslots: %s", checked_items)
    else:
        logger.warning("[CREATIVE] Timeslots multiselect widget not found")

    dialog_manager.dialog_data["ceremony_timeslots"] = checked_items
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

    # Delete media group if it was sent
    media_group_message_ids = dialog_manager.dialog_data.get("media_group_message_ids")
    if media_group_message_ids:
        try:
            for message_id in media_group_message_ids:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=message_id
                )
        except Exception as e:
            logger.error("[CREATIVE] Error deleting media group: %s", e)
        finally:
            # Clear media group IDs from dialog data
            dialog_manager.dialog_data.pop("media_group_message_ids", None)

    # Get selected items from Multiselect widget
    multiselect = dialog_manager.find("fair_roles_multiselect")
    checked_items = []
    if multiselect:
        checked_items = list(multiselect.get_checked())
        logger.info("[CREATIVE] Selected fair roles: %s", checked_items)
    else:
        logger.warning("[CREATIVE] Fair roles multiselect widget not found")

    dialog_manager.dialog_data["fair_roles"] = checked_items
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
    

    # Call placeholder functions
    await save_to_database(dialog_manager, user.id)

    await callback.message.answer(
        "✅ Спасибо! Твоя заявка принята."
    )

    await dialog_manager.switch_to(CreativeSelectionSG.success, show_mode=ShowMode.DELETE_AND_SEND)


# Placeholder functions for future implementation

async def save_to_database(manager: DialogManager, user_id: int) -> None:
    """
    Save creative selection application to database.

    Updates user_info table with:
    - full_name from dialog_data["creative_name"]
    - email from dialog_data["creative_email"]
    - education from dialog_data["creative_university"]
    (only if values are not blank)

    Inserts into creative_applications table with all collected data.
    """
    from app.infrastructure.database.database.db import DB
    from app.infrastructure.database.models.user_info import UsersInfoModel
    from app.infrastructure.database.models.creative_application import (
        CreativeApplicationModel,
    )

    db: DB | None = manager.middleware_data.get("db")
    if not db:
        logger.error("[CREATIVE] No database session available")
        return

    dialog_data = manager.dialog_data

    try:
        # Step 1: Update user_info conditionally
        existing_info = await db.users_info.get_user_info(user_id=user_id)

        # Extract new values from dialog
        new_name = dialog_data.get("creative_name", "").strip() or None
        new_email = dialog_data.get("creative_email", "").strip() or None
        new_education = dialog_data.get("creative_university", "").strip() or None

        # Build model preserving existing values when new ones are blank
        user_info = UsersInfoModel(
            user_id=user_id,
            full_name=new_name or (existing_info.full_name if existing_info else None),
            email=new_email or (existing_info.email if existing_info else None),
            education=new_education
            or (existing_info.education if existing_info else None),
            # Preserve other fields from existing record
            username=existing_info.username if existing_info else None,
            university_course=existing_info.university_course if existing_info else None,
            occupation=existing_info.occupation if existing_info else None,
        )

        await db.users_info.upsert(model=user_info)
        logger.info("[CREATIVE] Updated user_info for user=%d", user_id)

        # Step 2: Insert/update creative application
        direction = dialog_data.get("creative_direction", "")

        # Validate direction
        if direction not in ("ceremony", "fair"):
            logger.error("[CREATIVE] Invalid direction: %s", direction)
            return

        # Build application model based on direction
        application = CreativeApplicationModel(
            user_id=user_id,
            contact=dialog_data.get("creative_contact", ""),
            direction=direction,
            # Ceremony fields
            ceremony_stage_experience=dialog_data.get("ceremony_stage_experience")
            if direction == "ceremony"
            else None,
            ceremony_motivation=dialog_data.get("ceremony_motivation")
            if direction == "ceremony"
            else None,
            ceremony_can_attend_md=dialog_data.get("ceremony_can_attend_md")
            if direction == "ceremony"
            else None,
            ceremony_rehearsal_frequency=dialog_data.get("ceremony_rehearsal_frequency")
            if direction == "ceremony"
            else None,
            ceremony_rehearsal_duration=dialog_data.get("ceremony_rehearsal_duration")
            if direction == "ceremony"
            else None,
            ceremony_timeslots=dialog_data.get("ceremony_timeslots")
            if direction == "ceremony"
            else None,
            ceremony_cloud_link=dialog_data.get("ceremony_cloud_link")
            if direction == "ceremony"
            else None,
            # Fair fields
            fair_roles=dialog_data.get("fair_roles") if direction == "fair" else None,
            fair_motivation=dialog_data.get("fair_motivation")
            if direction == "fair"
            else None,
            fair_experience=dialog_data.get("fair_experience")
            if direction == "fair"
            else None,
            fair_cloud_link=dialog_data.get("fair_cloud_link")
            if direction == "fair"
            else None,
        )

        await db.creative_applications.upsert_application(model=application)
        logger.info(
            "[CREATIVE] Saved application for user=%d, direction=%s", user_id, direction
        )

        # Commit transaction
        await db.session.commit()

    except Exception as e:
        logger.error(
            "[CREATIVE] Failed to save application for user=%d: %s",
            user_id,
            e,
            exc_info=True,
        )
        # Rollback on error
        await db.session.rollback()
        raise

