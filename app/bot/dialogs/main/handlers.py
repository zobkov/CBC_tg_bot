"""Callback handlers for main dialog buttons."""

from __future__ import annotations

import logging

from aiogram.types import CallbackQuery, FSInputFile
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.database.db import DB
from app.services.participant_cert import (
    generate_cert,
    generate_cert_for_db_user,
    get_participant_info,
)
from app.utils.certificate_gen.generator import CertificateGenerationError
from app.utils.deadline_checker import (
    get_task_submission_status_message,
    is_task_submission_closed,
)
from app.bot.dialogs.grants.states import GrantsSG
from app.bot.dialogs.main.states import MainMenuSG

_LOGGER = logging.getLogger(__name__)

_FIRST_STAGE_DENIED_MESSAGE = (
    "Мы внимательно изучили более 300 заявок. Конкуренция была очень "
    "высокой, и к сожалению, на этот раз твой путь в рамках основного "
    "отбора на этом завершается. Это не приговор, это – точка роста, от "
    "которой можно (и нужно!) двигаться дальше. Мы будем рады видеть тебя "
    "на других активностях КБК'26.\n\n"
    "Мы верим в твой потенциал и хотим, чтобы ты продолжал раскрывать "
    "себя. В следующих заявках попробуй подробнее делиться тем, что для "
    "тебя действительно важно: опытом, мыслями, идеями, тем, что тебя "
    "вдохновляет. Позволь нам увидеть за строчками анкеты живого человека: "
    "твой характер, ценности и амбиции.\n"
    "Уверены, впереди ещё много пересечений и возможностей, где твоя "
    "уникальность сможет проявиться в полной мере.\n\n"
    "Никогда не останавливайся и смело двигайся вперёд, и мы уверены, что "
    "наши пути ещё обязательно пересекутся!"
)


async def _notify_first_stage_denied(callback: CallbackQuery) -> None:
    await callback.message.answer(_FIRST_STAGE_DENIED_MESSAGE)


async def _is_first_stage_accessible(dialog_manager: DialogManager) -> bool:
    db: DB | None = dialog_manager.middleware_data.get("db")
    event_from_user = dialog_manager.event.from_user

    if not db:
        return True

    try:
        evaluation = await db.evaluated_applications.get_evaluation(
            user_id=event_from_user.id,
        )
    except (SQLAlchemyError, AttributeError) as exc:
        _LOGGER.error(
            "Failed to fetch evaluation for user %s: %s",
            event_from_user.id,
            exc,
        )
        return True

    if evaluation is None:
        return False

    return any(
        (
            evaluation.accepted_1,
            evaluation.accepted_2,
            evaluation.accepted_3,
        )
    )






async def on_interview_button_clicked(
    callback: CallbackQuery,
    _button: Button,
    _dialog_manager: DialogManager,
) -> None:
    """Show a short alert explaining that interview booking is closed."""
    await callback.answer("Запись на интервью закрыта", show_alert=True)


async def on_grants_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """Route to the appropriate grants branch based on user_mentors record."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    user_id = callback.from_user.id

    target_state = GrantsSG.MAIN_GENERAL
    if db:
        try:
            record = await db.user_mentors.get_by_user_id(user_id=user_id)
            if record is not None:
                target_state = GrantsSG.MAIN_GSOM
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error(
                "on_grants_clicked: DB error for user %d: %s", user_id, exc
            )

    await dialog_manager.start(target_state)


async def on_participant_cert_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """Generate (or return cached) the participant certificate and send it.

    Fast path: user is in the CSV → generate immediately.
    Fallback: user is in bot_forum_registrations DB → ask gender first.
    """
    user_id = callback.from_user.id

    # Fast path: user is in CSV with known gender
    info = get_participant_info(user_id)
    if info is not None:
        await callback.answer("Генерирую сертификат…")
        try:
            cert_path = generate_cert(user_id)
        except CertificateGenerationError as exc:
            _LOGGER.error("Certificate generation failed for user %d: %s", user_id, exc)
            await callback.message.answer(
                "Не удалось сгенерировать сертификат. Пожалуйста, обратитесь к @cbc_assistant."
            )
            return
        await callback.message.answer_document(
            FSInputFile(cert_path),
            caption="🎓 Твой сертификат участника форума КБК'26",
        )
        return

    # DB fallback: user is registered in bot_forum_registrations but not in CSV
    db: DB | None = dialog_manager.middleware_data.get("db")
    reg = None
    if db:
        try:
            reg = await db.forum_registrations.get_by_user_id(user_id=user_id)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("on_participant_cert_clicked: DB error for user %d: %s", user_id, exc)

    if reg is None:
        await callback.answer(
            "Вы не найдены в списке участников форума.", show_alert=True
        )
        return

    dialog_manager.dialog_data["db_reg"] = dict(reg)
    await dialog_manager.switch_to(MainMenuSG.GENDER_SELECT)


async def _send_cert_for_db_user(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    gender: str,
) -> None:
    """Generate and send a cert for a DB-sourced user with the given gender."""
    user_id = callback.from_user.id
    reg = dialog_manager.dialog_data.get("db_reg") or {}
    full_name = (reg.get("name") or "").strip() or callback.from_user.full_name or "Участник"
    track = reg.get("track") or ""

    await callback.answer("Генерирую сертификат…")
    try:
        cert_path = generate_cert_for_db_user(
            user_id=user_id,
            full_name=full_name,
            gender=gender,
            track=track,
        )
    except CertificateGenerationError as exc:
        _LOGGER.error("Certificate generation failed for user %d: %s", user_id, exc)
        await callback.message.answer(
            "Не удалось сгенерировать сертификат. Пожалуйста, обратитесь к @cbc_assistant."
        )
        await dialog_manager.switch_to(MainMenuSG.MAIN)
        return

    await callback.message.answer_document(
        FSInputFile(cert_path),
        caption="🎓 Твой сертификат участника форума КБК'26",
    )
    await dialog_manager.switch_to(MainMenuSG.MAIN)


async def on_gender_m_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    await _send_cert_for_db_user(callback, dialog_manager, gender="M")


async def on_gender_f_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    await _send_cert_for_db_user(callback, dialog_manager, gender="F")
