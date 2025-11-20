from __future__ import annotations

import logging
from typing import Any

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select

from app.bot.states.feedback import FeedbackSG

logger = logging.getLogger(__name__)


async def on_task_selected(
    callback: Any,
    widget: Select,
    dialog_manager: DialogManager,
    task_id: str,
) -> None:
    """Store selected task and show details."""
    tasks = dialog_manager.dialog_data.get("tasks_cache", []) or []
    selected = next((task for task in tasks if task.get("task_id") == str(task_id)), None)
    if selected is None:
        logger.warning("Task feedback not found for id=%s", task_id)
        return

    dialog_manager.dialog_data["selected_task"] = selected
    await dialog_manager.switch_to(FeedbackSG.show_feedback)


async def on_back_to_tasks(_: Any, __: Button, dialog_manager: DialogManager) -> None:
    """Return to the tasks list preserving cache."""
    dialog_manager.dialog_data.pop("selected_task", None)
    await dialog_manager.switch_to(FeedbackSG.feedback_menu)
