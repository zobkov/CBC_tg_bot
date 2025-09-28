from aiogram.fsm.state import State, StatesGroup


class InterviewSG(StatesGroup):
    """Interview scheduling dialog states"""
    # Main interview menu
    main_menu = State()
    
    # Date selection
    date_selection = State()
    
    # Time slot selection for specific date
    time_selection = State()
    
    # Confirmation of selected timeslot
    confirmation = State()
    
    # Success/completion state
    success = State()
    
    # Reschedule flow states
    reschedule_menu = State()
    reschedule_date_selection = State()
    reschedule_time_selection = State()
    reschedule_confirmation = State()