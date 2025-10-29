"""
States для диалогов волонтёров
"""
from aiogram.fsm.state import State, StatesGroup


class VolunteerMenuSG(StatesGroup):
    """Состояния главного меню волонтёра"""
    MAIN = State()
    SUPPORT = State()
    HELP_USERS = State()