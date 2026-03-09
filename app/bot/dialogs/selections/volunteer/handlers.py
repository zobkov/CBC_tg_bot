"""Handlers for the volunteer selection dialog."""

import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.user_info import UsersInfoModel
from app.infrastructure.database.models.volunteer_application import VolunteerApplicationModel
from .states import VolunteerSelectionSG

logger = logging.getLogger(__name__)


# ─────────────── Navigation ───────────────

async def on_go_home(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Close dialog and return to main menu."""
    await callback.answer()
    await dialog_manager.done()


async def on_start_clicked(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Begin the application. Check existing user_info and decide where to start."""
    await callback.answer()
    dialog_manager.dialog_data.clear()

    db: DB | None = dialog_manager.middleware_data.get("db")
    user_id = callback.from_user.id

    if db:
        try:
            info = await db.users_info.get_user_info(user_id=user_id)
            if (
                info
                and info.full_name
                and info.email
                and info.education
            ):
                dialog_manager.dialog_data["vol_full_name"] = info.full_name
                dialog_manager.dialog_data["vol_email"] = info.email
                dialog_manager.dialog_data["vol_education"] = info.education
                await dialog_manager.switch_to(VolunteerSelectionSG.confirmation)
                return
        except Exception as exc:
            logger.error(
                "[VOLUNTEER] Failed to load user_info for user %d: %s",
                user_id,
                exc,
            )

    await dialog_manager.switch_to(VolunteerSelectionSG.name)


async def on_confirm_yes(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """User confirmed existing data; proceed to phone."""
    await callback.answer()
    await dialog_manager.switch_to(VolunteerSelectionSG.phone)


async def on_confirm_no(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """User wants to re-enter their data; go to name step."""
    await callback.answer()
    await dialog_manager.switch_to(VolunteerSelectionSG.name)


# ─────────────── Personal info ───────────────

async def on_name_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_full_name"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.email)


async def on_email_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_email"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.education)


async def on_education_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_education"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.phone)


# ─────────────── Compulsory ───────────────

async def on_phone_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_phone"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.volunteer_dates)


async def on_dates_single(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_volunteer_dates"] = "single"
    await dialog_manager.switch_to(VolunteerSelectionSG.function)


async def on_dates_double(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_volunteer_dates"] = "double"
    await dialog_manager.switch_to(VolunteerSelectionSG.function)


async def on_function_general(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_function"] = "general"
    await dialog_manager.switch_to(VolunteerSelectionSG.general_1)


async def on_function_photo(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_function"] = "photo"
    await dialog_manager.switch_to(VolunteerSelectionSG.photo_1)


async def on_function_translate(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_function"] = "translate"
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_1)


# ─────────────── General branch ───────────────

async def on_general_1_guest(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_general_1_type"] = "guest"
    await dialog_manager.switch_to(VolunteerSelectionSG.general_1_1)


async def on_general_1_volunteer(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_general_1_type"] = "volunteer"
    await dialog_manager.switch_to(VolunteerSelectionSG.general_1_2)


async def on_general_1_both(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_general_1_type"] = "guest_and_volunteer"
    await dialog_manager.switch_to(VolunteerSelectionSG.general_1_3)


async def on_general_1_no(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_general_1_type"] = "no"
    await dialog_manager.switch_to(VolunteerSelectionSG.general_2)


async def on_general_1_answer_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """All three sub-states share the same DB field."""
    dialog_manager.dialog_data["vol_general_1_answer"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.general_2)


async def on_general_2_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_general_2"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.general_3)


async def on_general_3_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_general_3"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.additional_information_prompt)


# ─────────────── Photo branch ───────────────

async def on_photo_1_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_photo_portfolio"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.photo_2)


async def on_photo_equipment_yes(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_photo_has_equipment"] = "yes"
    await dialog_manager.switch_to(VolunteerSelectionSG.photo_3)


async def on_photo_equipment_no(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_photo_has_equipment"] = "no"
    await dialog_manager.switch_to(VolunteerSelectionSG.photo_3)


async def on_photo_3_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_photo_experience"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.photo_4)


async def on_photo_4_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_photo_key_moments"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.additional_information_prompt)


# ─────────────── Translation branch ───────────────

async def on_translate_1_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_translate_level"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_2)


async def on_translate_cert_yes(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_translate_has_cert"] = "yes"
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_2_certificate)


async def on_translate_cert_no(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["vol_translate_has_cert"] = "no"
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_3)


async def on_translate_cert_link_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_translate_cert_link"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_3)


async def on_translate_experience_yes(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_3_1)


async def on_translate_experience_no(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_4)


async def on_translate_3_1_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_translate_experience_detail"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_3_2)


async def on_translate_3_2_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_translate_worked_with_foreigners"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.translate_4)


async def on_translate_4_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vol_translate_difficult_situation"] = value.strip()
    await dialog_manager.switch_to(VolunteerSelectionSG.additional_information_prompt)


# ─────────────── Ending ───────────────

# Map role key → dialog_data key for per-role additional information
_ROLE_ADD_INFO_KEY = {
    "general": "vol_general_additional_information",
    "photo": "vol_photo_additional_information",
    "translate": "vol_translate_additional_information",
}


async def _save_application(dialog_manager: DialogManager) -> None:
    """Persist user_info and volunteer application to the database.

    If ``dialog_data["is_additional_role"]`` is True the new role data is
    merged into the existing DB row; otherwise a full upsert is performed.
    """
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = dialog_manager.event
    user_id = event.from_user.id if event and event.from_user else None

    if not db or not user_id:
        logger.error("[VOLUNTEER] Cannot save application: db=%s, user_id=%s", db, user_id)
        return

    data = dialog_manager.dialog_data
    is_additional_role: bool = bool(data.get("is_additional_role", False))
    current_role: str = data.get("vol_function", "") or ""

    # Determine per-role additional_information field
    add_info_key = _ROLE_ADD_INFO_KEY.get(current_role, "vol_additional_information")

    # Always update user_info when personal data is present
    full_name = data.get("vol_full_name")
    email = data.get("vol_email")
    education = data.get("vol_education")
    phone = data.get("vol_phone")
    if full_name or email or education or phone:
        await db.users_info.upsert(
            model=UsersInfoModel(
                user_id=user_id,
                full_name=full_name,
                email=email,
                education=education,
                phone=phone,
            )
        )

    role_model = VolunteerApplicationModel(
        user_id=user_id,
        phone=data.get("vol_phone"),
        volunteer_dates=data.get("vol_volunteer_dates"),
        function=current_role,
        general_1_type=data.get("vol_general_1_type"),
        general_1_answer=data.get("vol_general_1_answer"),
        general_2=data.get("vol_general_2"),
        general_3=data.get("vol_general_3"),
        general_additional_information=data.get("vol_general_additional_information"),
        photo_portfolio=data.get("vol_photo_portfolio"),
        photo_has_equipment=data.get("vol_photo_has_equipment"),
        photo_experience=data.get("vol_photo_experience"),
        photo_key_moments=data.get("vol_photo_key_moments"),
        photo_additional_information=data.get("vol_photo_additional_information"),
        translate_level=data.get("vol_translate_level"),
        translate_has_cert=data.get("vol_translate_has_cert"),
        translate_cert_link=data.get("vol_translate_cert_link"),
        translate_experience_detail=data.get("vol_translate_experience_detail"),
        translate_worked_with_foreigners=data.get("vol_translate_worked_with_foreigners"),
        translate_difficult_situation=data.get("vol_translate_difficult_situation"),
        translate_additional_information=data.get("vol_translate_additional_information"),
        additional_information=data.get("vol_additional_information"),
    )

    if is_additional_role:
        await db.volunteer_applications.merge_role(
            user_id=user_id,
            new_role_model=role_model,
        )
    else:
        await db.volunteer_applications.upsert_application(model=role_model)

    logger.info(
        "[VOLUNTEER] Application saved for user_id=%d (additional_role=%s, function=%s)",
        user_id,
        is_additional_role,
        current_role,
    )


async def on_additional_info_entered(
    _message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    """Save additional info into the correct per-role key, persist, then show END."""
    current_role: str = dialog_manager.dialog_data.get("vol_function", "") or ""
    add_info_key = _ROLE_ADD_INFO_KEY.get(current_role, "vol_additional_information")
    dialog_manager.dialog_data[add_info_key] = value.strip()
    await _save_application(dialog_manager)
    await dialog_manager.switch_to(VolunteerSelectionSG.END)


# ─────────────── Multi-role ───────────────

async def on_another_role_clicked(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """User wants to apply for an additional role. Preserve existing dialog_data."""
    await callback.answer()
    dialog_manager.dialog_data["is_additional_role"] = True
    await dialog_manager.switch_to(VolunteerSelectionSG.another_role)


def _roles_from_dialog(dialog_manager: DialogManager) -> set[str]:
    """Return roles already stored in dialog_data (filled_roles from getter)."""
    # filled_roles is populated by get_another_role_data getter; may not be in
    # dialog_data itself so we check middleware / start_data fallback.
    return set()


async def _start_role(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    role: str,
    first_state: Any,
) -> None:
    """Common logic when user selects a role from another_role window."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    user_id = callback.from_user.id

    # Check whether this role is already filled
    already_filled = False
    if db:
        try:
            existing = await db.volunteer_applications.get_application(user_id=user_id)
            if existing:
                filled = {r.strip() for r in (existing.function or "").split(",") if r.strip()}
                already_filled = role in filled
        except Exception as exc:
            logger.error("[VOLUNTEER] _start_role check failed: %s", exc)

    if already_filled:
        dialog_manager.dialog_data["overwriting_role"] = role
        await dialog_manager.switch_to(VolunteerSelectionSG.overwrite_confirm)
        return

    # Clear stale role-specific data for the chosen role
    dialog_manager.dialog_data["vol_function"] = role
    _clear_role_data(dialog_manager, role)
    await dialog_manager.switch_to(first_state)


def _clear_role_data(dialog_manager: DialogManager, role: str) -> None:
    """Remove dialog_data keys belonging to the given role branch."""
    data = dialog_manager.dialog_data
    if role == "general":
        for k in ("vol_general_1_type", "vol_general_1_answer", "vol_general_2",
                  "vol_general_3", "vol_general_additional_information"):
            data.pop(k, None)
    elif role == "photo":
        for k in ("vol_photo_portfolio", "vol_photo_has_equipment", "vol_photo_experience",
                  "vol_photo_key_moments", "vol_photo_additional_information"):
            data.pop(k, None)
    elif role == "translate":
        for k in ("vol_translate_level", "vol_translate_has_cert", "vol_translate_cert_link",
                  "vol_translate_experience_detail", "vol_translate_worked_with_foreigners",
                  "vol_translate_difficult_situation", "vol_translate_additional_information"):
            data.pop(k, None)


async def on_another_select_general(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await _start_role(callback, dialog_manager, "general", VolunteerSelectionSG.general_1)


async def on_another_select_photo(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await _start_role(callback, dialog_manager, "photo", VolunteerSelectionSG.photo_1)


async def on_another_select_translate(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await _start_role(callback, dialog_manager, "translate", VolunteerSelectionSG.translate_1)


async def on_overwrite_confirm_yes(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """User confirmed overwriting an already-filled role."""
    await callback.answer()
    role = dialog_manager.dialog_data.pop("overwriting_role", "")
    dialog_manager.dialog_data["vol_function"] = role
    _clear_role_data(dialog_manager, role)
    state_map = {
        "general": VolunteerSelectionSG.general_1,
        "photo": VolunteerSelectionSG.photo_1,
        "translate": VolunteerSelectionSG.translate_1,
    }
    await dialog_manager.switch_to(state_map[role])


async def on_overwrite_confirm_no(
    callback: CallbackQuery,
    _button: Any,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """User cancelled overwriting; go back to role selection."""
    await callback.answer()
    dialog_manager.dialog_data.pop("overwriting_role", None)
    await dialog_manager.switch_to(VolunteerSelectionSG.another_role)
