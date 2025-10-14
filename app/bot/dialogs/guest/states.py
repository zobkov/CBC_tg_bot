"""
States для диалогов гостей
"""
from aiogram.fsm.state import State, StatesGroup


class GuestMenuSG(StatesGroup):
    """Состояния главного меню гостя"""
    MAIN = State()
    SUPPORT = State()