"""States for the creative selection part 2 (fair questionnaire) dialog."""

from aiogram.fsm.state import State, StatesGroup


class CreativeSelectionPart2SG(StatesGroup):
    MAIN = State()
    question_1 = State()
    question_2 = State()
    question_3 = State()
    question_4 = State()
    question_5 = State()
    question_6 = State()
    confirmation = State()
    success = State()
