"""Callback handlers for guest dialog buttons."""

from __future__ import annotations

import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from sqlalchemy.exc import SQLAlchemyError

from app.bot.states.main_menu import MainMenuSG
from app.bot.states.tasks import TasksSG
from app.infrastructure.database.database.db import DB
from app.utils.deadline_checker import (
    get_task_submission_status_message,
    is_task_submission_closed,
)

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


async def on_current_stage_clicked(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """Open task dialog if submissions are available for the user."""
    await callback.answer()

    if is_task_submission_closed():
        await callback.message.answer(get_task_submission_status_message())
        return

    if not await _is_first_stage_accessible(dialog_manager):
        await _notify_first_stage_denied(callback)
        return

    await dialog_manager.start(state=TasksSG.main)


async def on_support_clicked(
    _callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
) -> None:
    """Switch to the support screen."""
    await dialog_manager.switch_to(state=MainMenuSG.support)


async def on_interview_button_clicked(
    callback: CallbackQuery,
    _button: Button,
    _dialog_manager: DialogManager,
) -> None:
    """Show a short alert explaining that interview booking is closed."""
    await callback.answer("Запись на интервью закрыта", show_alert=True)
