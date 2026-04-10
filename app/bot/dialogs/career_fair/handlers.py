"""Handlers для диалога Ярмарки карьеры."""
import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from .states import CareerFairSG

logger = logging.getLogger(__name__)


async def on_track_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    """Stores the selected track key and navigates to company list."""
    manager.dialog_data["selected_track"] = item_id
    await manager.switch_to(CareerFairSG.COMPANY_LIST)


async def on_company_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    """Stores the selected company key and navigates to company detail."""
    manager.dialog_data["selected_company"] = item_id
    await manager.switch_to(CareerFairSG.COMPANY_DETAIL)
