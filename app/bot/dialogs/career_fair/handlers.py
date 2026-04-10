"""Handlers для диалога Ярмарки карьеры."""
import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB

from .states import CareerFairSG

logger = logging.getLogger(__name__)


async def on_track_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    """Stores the selected track key, logs a stat event, navigates to company list."""
    manager.dialog_data["selected_track"] = item_id

    db: DB | None = manager.middleware_data.get("db")
    if db:
        try:
            await db.career_fair_stats.log_event(
                user_id=callback.from_user.id,
                event_type="track_view",
                track_key=item_id,
            )
        except Exception as exc:
            logger.warning("career_fair_stats log_event failed: %s", exc)

    await manager.switch_to(CareerFairSG.COMPANY_LIST)


async def on_company_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    """Stores the selected company key, logs a stat event, navigates to company detail."""
    manager.dialog_data["selected_company"] = item_id

    db: DB | None = manager.middleware_data.get("db")
    if db:
        try:
            track_key = manager.dialog_data.get("selected_track")
            await db.career_fair_stats.log_event(
                user_id=callback.from_user.id,
                event_type="company_view",
                track_key=track_key,
                company_key=item_id,
            )
        except Exception as exc:
            logger.warning("career_fair_stats log_event failed: %s", exc)

    await manager.switch_to(CareerFairSG.COMPANY_DETAIL)


async def on_vacancies_clicked(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
) -> None:
    """Logs a vacancies_view stat event and navigates to vacancies window."""
    db: DB | None = manager.middleware_data.get("db")
    if db:
        try:
            await db.career_fair_stats.log_event(
                user_id=callback.from_user.id,
                event_type="vacancies_view",
                track_key=manager.dialog_data.get("selected_track"),
                company_key=manager.dialog_data.get("selected_company"),
            )
        except Exception as exc:
            logger.warning("career_fair_stats log_event failed: %s", exc)

    await manager.switch_to(CareerFairSG.COMPANY_VACANCIES)
