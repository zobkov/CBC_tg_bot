"""FSM states for the volunteer review dialog."""

from aiogram.fsm.state import State, StatesGroup


class VolReviewSG(StatesGroup):
    PAGE_SELECT = State()   # Grid of page number buttons
    PAGE = State()          # List of 10 applications on the selected page
    APP_DETAIL = State()    # Full text answers (paginated when text exceeds TG limit)
    VIDEO = State()         # Video interview – 3 circles sent then shown
