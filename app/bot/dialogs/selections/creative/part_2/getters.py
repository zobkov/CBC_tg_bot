"""Getters for the creative selection part 2 dialog."""

from typing import Any

from aiogram_dialog import DialogManager


async def get_part2_confirmation_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return answers from dialog_data for the confirmation summary window."""
    dd = dialog_manager.dialog_data
    return {
        "q1": dd.get("part2_q1", "—"),
        "q2": dd.get("part2_q2", "—"),
        "q3": dd.get("part2_q3", "—"),
        "q4": dd.get("part2_q4", "—"),
        "q5": dd.get("part2_q5", "—"),
        "q6": dd.get("part2_q6", "—"),
    }
