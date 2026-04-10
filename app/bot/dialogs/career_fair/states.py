"""States для диалога Ярмарки карьеры."""
from aiogram.fsm.state import State, StatesGroup


class CareerFairSG(StatesGroup):
    """State definitions for career fair dialog screens."""
    MAIN = State()               # Track selection
    COMPANY_LIST = State()       # Companies in selected track
    COMPANY_DETAIL = State()     # Company image + description
    COMPANY_VACANCIES = State()  # Vacancy links (text-only, 4096 char limit)
