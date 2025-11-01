from aiogram.fsm.state import State, StatesGroup


class QuizDodSG(StatesGroup):
    # note on naming: small letters for single use windows; capital letters for multiple use windows
    # either dynamic ones or main-menu-like
    MAIN = State()
    name = State()
    phone = State()
    email = State()
    QUESTIONS = State()
    RESULTS = State()