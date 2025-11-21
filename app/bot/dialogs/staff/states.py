"""
States для диалогов сотрудников
"""
from aiogram.fsm.state import State, StatesGroup


class StaffMenuSG(StatesGroup): # pylint: disable=too-few-public-methods
    """Состояния главного меню сотрудника"""
    MAIN = State()
    support = State()
