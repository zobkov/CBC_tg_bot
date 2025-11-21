"""FSM states used by the quiz dialog."""

from aiogram.fsm.state import State, StatesGroup


class QuizDodSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """Lowercase names are single-use windows, uppercase ones are reusable."""

    MAIN = State()
    name = State()
    phone = State()
    email = State()
    education = State()
    QUESTIONS = State()
    RESULTS = State()
