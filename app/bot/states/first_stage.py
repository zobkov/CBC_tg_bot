from aiogram.fsm.state import State, StatesGroup


class FirstStageSG(StatesGroup):
    # Информация о первом этапе
    stage_info = State()
    
    # Форма анкеты
    full_name = State()
    university = State()
    course = State()
    phone = State()
    email = State()
    how_found_kbk = State()
    department = State()
    position = State()
    experience = State()
    motivation = State()
    resume_upload = State()
    
    # Подтверждение
    confirmation = State()
    success = State()
