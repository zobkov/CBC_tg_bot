"""
States для диалога настроек
"""
from aiogram.fsm.state import State, StatesGroup


class SettingsSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """State definitions for settings dialog screens."""
    MAIN = State()
    PROFILE = State()
    SUPPORT = State()
    edit_name = State()
    edit_education = State()
    edit_email = State()
