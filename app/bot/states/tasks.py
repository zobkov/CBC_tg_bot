from aiogram.fsm.state import State, StatesGroup


class TasksSG(StatesGroup):
    main = State()
    task_1 = State()
    task_1_upload = State()
    task_1_submitted = State()
    task_2 = State()
    task_2_upload = State()
    task_2_submitted = State()
    task_3 = State()
    task_3_upload = State()
    task_3_submitted = State()
