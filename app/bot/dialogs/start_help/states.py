"""States for the start_help onboarding dialog."""
from aiogram.fsm.state import State, StatesGroup


class StartHelpSG(StatesGroup):
    want_reg = State()
    site_reg = State()
    need_reg = State()
    id_enter = State()
    wrong_code = State()
    fio_enter = State()
    fio_not_found = State()
    email_enter = State()
    email_wrong = State()
