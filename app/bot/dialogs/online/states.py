"""
States для диалога онлайн-лекций
"""
from aiogram.fsm.state import State, StatesGroup


class OnlineSG(StatesGroup):
    """State definitions for online lectures dialog screens."""
    MAIN = State()
    SCHEDULE = State()
    SCHEDULE_EVENT = State()
    MY_EVENTS = State()
    MY_EVENT_DETAIL = State()
    SUPPORT = State()
    SUCCESSFUL_REGISTRATION = State()
