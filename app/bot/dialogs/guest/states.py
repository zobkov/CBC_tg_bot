"""
States для диалогов гостей
"""
from aiogram.fsm.state import State, StatesGroup


class GuestMenuSG(StatesGroup):
    MAIN = State()
    current_stage_info = State()
    support = State()
    not_availabe = State()
