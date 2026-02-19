"""
States general registration 
"""
from aiogram.fsm.state import State, StatesGroup


class RegistrationSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """State definitions for registration sequence dialog screens."""
    MAIN = State()
    name = State()
    university = State()
    email = State()
