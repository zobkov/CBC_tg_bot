from aiogram.fsm.state import State, StatesGroup


class FeedbackSG(StatesGroup):
    """Feedback dialog states"""
    # Main feedback menu with available feedback buttons
    feedback_menu = State()
    
    # Show specific feedback for a position
    show_feedback = State()