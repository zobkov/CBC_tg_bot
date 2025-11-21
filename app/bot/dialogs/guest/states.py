"""
States для диалогов гостей
"""
from aiogram.fsm.state import State, StatesGroup


class GuestMenuSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """State definitions for guest menu dialog screens."""
    MAIN = State()
    current_stage_info = State()
    support = State()
    not_availabe = State()
