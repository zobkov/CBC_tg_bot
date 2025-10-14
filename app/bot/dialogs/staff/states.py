"""
States для диалогов сотрудников
"""
from aiogram.fsm.state import State, StatesGroup


class StaffMenuSG(StatesGroup):
    """Состояния главного меню сотрудника"""
    MAIN = State()
    SUPPORT = State()
    APPLICATIONS = State()