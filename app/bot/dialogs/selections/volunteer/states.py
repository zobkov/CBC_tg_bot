"""FSM states for the volunteer selection dialog."""

from aiogram.fsm.state import State, StatesGroup


class VolunteerSelectionSG(StatesGroup):
    """States for the volunteer application flow."""

    # Entry point
    MAIN = State()

    # General info confirmation
    confirmation = State()

    # Personal info collection
    name = State()
    email = State()
    education = State()

    # Compulsory questions
    phone = State()
    volunteer_dates = State()
    function = State()

    # General branch
    general_1 = State()
    general_1_1 = State()
    general_1_2 = State()
    general_1_3 = State()
    general_2 = State()
    general_3 = State()

    # Photo branch
    photo_1 = State()
    photo_2 = State()
    photo_3 = State()
    photo_4 = State()

    # Translation branch
    translate_1 = State()
    translate_2 = State()
    translate_2_certificate = State()
    translate_3 = State()
    translate_3_1 = State()
    translate_3_2 = State()
    translate_4 = State()

    # Ending
    additional_information_prompt = State()
    END = State()

    # Multi-role: second application flow
    another_role = State()
    overwrite_confirm = State()
