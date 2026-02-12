"""FSM states for the creative selection (casting) dialog."""

from aiogram.fsm.state import State, StatesGroup


class CreativeSelectionSG(StatesGroup):  # pylint: disable=too-few-public-methods
    """
    States for the casting application flow.

    Lowercase names are single-use windows, uppercase ones are reusable.
    """

    # Entry point
    MAIN = State()

    # Common questions (all applicants)
    name = State()
    contact = State()
    email = State()
    university = State()
    direction_selection = State()

    # Branch A - Ceremony (Церемония открытия)
    ceremony_stage_experience = State()
    ceremony_motivation = State()
    ceremony_rehearsal_attendance = State()
    ceremony_rehearsal_frequency = State()
    ceremony_rehearsal_duration = State()
    ceremony_rehearsal_timeslots = State()
    ceremony_cloud_link = State()

    # Branch B - Fair (Ярмарка культуры)
    fair_role_selection = State()
    fair_role_motivation = State()
    fair_role_experience = State()
    fair_cloud_link = State()

    # Final states
    confirmation = State()
    success = State()
