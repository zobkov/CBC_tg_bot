"""Handlers for the volunteer selection part 2 dialog."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from .states import VolSelPart2SG

logger = logging.getLogger(__name__)

_MAX_LEN = 4000
_TOO_LONG = (
    f"⚠️ Ответ слишком длинный (максимум {_MAX_LEN} символов). "
    "Сократи текст и отправь снова."
)


# ── Navigation ────────────────────────────────────────────────────────────────

async def on_proceed_to_timer(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await dialog_manager.switch_to(VolSelPart2SG.timer_warning)


async def on_start_yes(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()

    from app.services.vol_part2_timer import (
        schedule_user_timer,
        STARTED_TEXT,
        TEST_DURATION_MIN,
        MSK_OFFSET,
    )

    user_id = callback.from_user.id
    bot_token = callback.bot.token
    now_utc = datetime.now(tz=timezone.utc)
    now_msk = now_utc + MSK_OFFSET
    deadline_msk = now_msk + timedelta(minutes=TEST_DURATION_MIN)

    schedule_user_timer(user_id, bot_token)
    await callback.message.answer(
        STARTED_TEXT.format(
            started=now_msk.strftime("%H:%M"),
            deadline=deadline_msk.strftime("%H:%M"),
        ),
        parse_mode="HTML",
    )

    await dialog_manager.switch_to(VolSelPart2SG.q1)


async def on_start_no(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await dialog_manager.switch_to(VolSelPart2SG.MAIN)


# ── Q1 – КБК ordinal (button choice) ─────────────────────────────────────────

async def on_q1_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    # Button ids: q1_1, q1_2, … q1_5 → extract ordinal label from id
    _btn_to_label = {
        "q1_1": "1ый",
        "q1_2": "2ой",
        "q1_3": "3ий",
        "q1_4": "4ый",
        "q1_5": "5ый",
    }
    label = _btn_to_label.get(button.widget_id, button.widget_id)
    dialog_manager.dialog_data["q1_kbc_ordinal"] = label
    await dialog_manager.switch_to(VolSelPart2SG.q2)


# ── Q2–Q6 text inputs ─────────────────────────────────────────────────────────

async def on_q2_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["q2_kbc_date"] = value.strip()
    await dialog_manager.switch_to(VolSelPart2SG.q3)


async def on_q3_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["q3_kbc_theme"] = value.strip()
    await dialog_manager.switch_to(VolSelPart2SG.q4)


async def on_q4_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    if len(value) > _MAX_LEN:
        await message.answer(_TOO_LONG)
        return
    dialog_manager.dialog_data["q4_team_experience"] = value.strip()
    await dialog_manager.switch_to(VolSelPart2SG.q5)


async def on_q5_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    if len(value) > _MAX_LEN:
        await message.answer(_TOO_LONG)
        return
    dialog_manager.dialog_data["q5_badge_case"] = value.strip()
    await dialog_manager.switch_to(VolSelPart2SG.q6)


async def on_q6_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    if len(value) > _MAX_LEN:
        await message.answer(_TOO_LONG)
        return
    dialog_manager.dialog_data["q6_foreign_guest_case"] = value.strip()
    await dialog_manager.switch_to(VolSelPart2SG.q7)


# ── Q7 – tour branch ──────────────────────────────────────────────────────────

async def on_q7_yes(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["q7_want_tour"] = "yes"
    await dialog_manager.switch_to(VolSelPart2SG.q7_experience)


async def on_q7_no(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["q7_want_tour"] = "no"
    await dialog_manager.switch_to(VolSelPart2SG.video_intro)


async def on_q7_experience_yes(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["q7_has_tour_experience"] = "yes"
    await dialog_manager.switch_to(VolSelPart2SG.q7_route)


async def on_q7_experience_no(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    dialog_manager.dialog_data["q7_has_tour_experience"] = "no"
    await dialog_manager.switch_to(VolSelPart2SG.q7_route)


async def on_q7_route_entered(
    message: Message,
    _widget: Any,
    dialog_manager: DialogManager,
    value: str,
    **_kwargs: Any,
) -> None:
    if len(value) > _MAX_LEN:
        await message.answer(_TOO_LONG)
        return
    dialog_manager.dialog_data["q7_tour_route"] = value.strip()
    await dialog_manager.switch_to(VolSelPart2SG.video_intro)


# ── Video intro ───────────────────────────────────────────────────────────────

async def on_video_proceed(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await callback.answer()
    await dialog_manager.switch_to(VolSelPart2SG.vq1)


# ── Video note handlers ───────────────────────────────────────────────────────

async def on_wrong_content_type(
    message: Message,
    _widget: Any,
    _dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    await message.answer(
        "⚠️ Пожалуйста, отправь именно <b>видео-кружок</b> (видеосообщение). "
        "Другой тип файла не принимается."
    )


async def on_vq1(
    message: Message,
    _widget: MessageInput,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vq1_file_id"] = message.video_note.file_id
    await dialog_manager.switch_to(VolSelPart2SG.vq2)


async def on_vq2(
    message: Message,
    _widget: MessageInput,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vq2_file_id"] = message.video_note.file_id
    await dialog_manager.switch_to(VolSelPart2SG.vq3)


async def on_vq3(
    message: Message,
    _widget: MessageInput,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    dialog_manager.dialog_data["vq3_file_id"] = message.video_note.file_id

    user_id = message.from_user.id

    from app.services.vol_part2_timer import cancel_user_timer
    cancel_user_timer(user_id)

    try:
        await _save_to_db(dialog_manager, user_id)
    except Exception as exc:
        logger.error(
            "[VOL_PART2] Failed to save for user_id=%d: %s", user_id, exc, exc_info=True
        )
        await message.answer(
            "❌ Произошла ошибка при сохранении ответов. Попробуй ещё раз или напиши @zobko."
        )
        return

    await dialog_manager.switch_to(VolSelPart2SG.success, show_mode=ShowMode.DELETE_AND_SEND)


# ── DB persistence ────────────────────────────────────────────────────────────

async def _save_to_db(dialog_manager: DialogManager, user_id: int) -> None:
    from app.infrastructure.database.database.db import DB
    from app.infrastructure.database.models.volunteer_selection_part2 import VolSelPart2Model

    db: DB | None = dialog_manager.middleware_data.get("db")
    if not db:
        logger.error("[VOL_PART2] No db in middleware_data for user_id=%d", user_id)
        return

    dd = dialog_manager.dialog_data
    model = VolSelPart2Model(
        user_id=user_id,
        q1_kbc_ordinal=dd.get("q1_kbc_ordinal"),
        q2_kbc_date=dd.get("q2_kbc_date"),
        q3_kbc_theme=dd.get("q3_kbc_theme"),
        q4_team_experience=dd.get("q4_team_experience"),
        q5_badge_case=dd.get("q5_badge_case"),
        q6_foreign_guest_case=dd.get("q6_foreign_guest_case"),
        q7_want_tour=dd.get("q7_want_tour"),
        q7_has_tour_experience=dd.get("q7_has_tour_experience"),
        q7_tour_route=dd.get("q7_tour_route"),
        vq1_file_id=dd.get("vq1_file_id"),
        vq2_file_id=dd.get("vq2_file_id"),
        vq3_file_id=dd.get("vq3_file_id"),
    )
    await db.volunteer_selection_part2.upsert(model=model)
    logger.info("[VOL_PART2] Saved answers for user_id=%d", user_id)
