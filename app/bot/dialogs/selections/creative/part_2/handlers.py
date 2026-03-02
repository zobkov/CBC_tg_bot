"""Handlers for the creative selection part 2 (fair questionnaire) dialog."""

import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from .states import CreativeSelectionPart2SG

logger = logging.getLogger(__name__)


# ── Generic text-input helpers ────────────────────────────────────────────────

async def _store_and_next(dialog_manager: DialogManager, key: str, value: str) -> None:
    dialog_manager.dialog_data[key] = value.strip()
    await dialog_manager.next()


async def on_q1_entered(
    _message: Message, _widget: Any, dialog_manager: DialogManager, value: str, **_kwargs: Any
) -> None:
    await _store_and_next(dialog_manager, "part2_q1", value)


async def on_q2_entered(
    _message: Message, _widget: Any, dialog_manager: DialogManager, value: str, **_kwargs: Any
) -> None:
    await _store_and_next(dialog_manager, "part2_q2", value)


async def on_q3_entered(
    _message: Message, _widget: Any, dialog_manager: DialogManager, value: str, **_kwargs: Any
) -> None:
    await _store_and_next(dialog_manager, "part2_q3", value)


async def on_q4_entered(
    _message: Message, _widget: Any, dialog_manager: DialogManager, value: str, **_kwargs: Any
) -> None:
    await _store_and_next(dialog_manager, "part2_q4", value)


async def on_q5_entered(
    _message: Message, _widget: Any, dialog_manager: DialogManager, value: str, **_kwargs: Any
) -> None:
    await _store_and_next(dialog_manager, "part2_q5", value)


async def on_q6_entered(
    _message: Message, _widget: Any, dialog_manager: DialogManager, value: str, **_kwargs: Any
) -> None:
    dialog_manager.dialog_data["part2_q6"] = value.strip()
    await dialog_manager.switch_to(CreativeSelectionPart2SG.confirmation)


# ── Submission ────────────────────────────────────────────────────────────────

async def on_submit_part2(
    callback: CallbackQuery,
    _button: Button,
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> None:
    """Save part 2 answers to DB and proceed to success screen."""
    await callback.answer()

    user = callback.from_user
    if not user:
        await callback.message.answer("Ошибка: не удалось определить пользователя")
        return

    try:
        await _save_part2_to_database(dialog_manager, user.id)
    except ValueError:
        await callback.message.answer(
            "❌ Не удалось сохранить ответы: заявка первого этапа не найдена. "
            "Обратитесь к организаторам."
        )
        return
    except Exception:
        await callback.message.answer(
            "❌ Произошла ошибка при сохранении ответов. Попробуйте ещё раз."
        )
        return

    await dialog_manager.switch_to(
        CreativeSelectionPart2SG.success, show_mode=ShowMode.DELETE_AND_SEND
    )


async def _save_part2_to_database(manager: DialogManager, user_id: int) -> None:
    from app.infrastructure.database.database.db import DB

    db: DB | None = manager.middleware_data.get("db")
    if not db:
        logger.error("[PART2] No database session available")
        return

    dd = manager.dialog_data
    try:
        await db.creative_applications.update_part2_fields(
            user_id=user_id,
            open_q1=dd.get("part2_q1"),
            open_q2=dd.get("part2_q2"),
            open_q3=dd.get("part2_q3"),
            case_q1=dd.get("part2_q4"),
            case_q2=dd.get("part2_q5"),
            case_q3=dd.get("part2_q6"),
        )
        # No flush needed — the middleware's session.begin() commits on exit.
        logger.info("[PART2] Saved part2 answers for user=%d", user_id)
    except ValueError as exc:
        # No matching row in creative_applications — surface to the user.
        logger.error("[PART2] Application not found for user=%d: %s", user_id, exc)
        raise
    except Exception as exc:
        logger.error("[PART2] Failed to save for user=%d: %s", user_id, exc, exc_info=True)
        raise
