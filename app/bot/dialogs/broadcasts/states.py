"""
States для диалогов гостей
"""
from aiogram.fsm.state import State, StatesGroup


class BroadcastMenuSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """State definitions for broadcast menu dialog screens."""
    MAIN = State()
