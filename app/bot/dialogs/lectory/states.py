"""FSM state group for the lectory (lecture schedule) dialog."""
from aiogram.fsm.state import State, StatesGroup


class LectorySG(StatesGroup):
    SCHEDULE = State()
    EVENT_DETAIL = State()
    ASK_QUESTION = State()
    MY_QUESTIONS = State()
