"""FSM state group for the forum dialog."""
from aiogram.fsm.state import State, StatesGroup


class ForumSG(StatesGroup):
    MAIN = State()
    tracks_info = State()
    change_track = State()
    way = State()
