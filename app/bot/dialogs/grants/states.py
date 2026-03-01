from aiogram.fsm.state import State, StatesGroup


class GrantsSG(StatesGroup):
    MAIN_GENERAL = State()
    MAIN_GSOM = State()
    GRANT_INFO = State()
    COURSE = State()
    FAQ = State()
    GRANT_INFO_GSOM = State()
    COURSE_GSOM = State()
    FAQ_GSOM = State()
    MENTOR = State()
    LESSON = State()
