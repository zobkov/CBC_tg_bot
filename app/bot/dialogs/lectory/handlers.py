"""Handlers for the lectory dialog."""
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from .states import LectorySG


async def on_event_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    """Store selected event key and navigate to event detail."""
    manager.dialog_data["selected_event"] = item_id
    await manager.switch_to(LectorySG.EVENT_DETAIL)
