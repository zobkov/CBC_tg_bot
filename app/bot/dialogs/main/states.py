"""
States для главного диалога
"""
from aiogram.fsm.state import State, StatesGroup


class MainMenuSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """State definitions for main menu dialog screens."""
    MAIN = State()
    current_stage_info = State()
    support = State()
    not_availabe = State()
