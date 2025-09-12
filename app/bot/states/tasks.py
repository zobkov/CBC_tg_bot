from aiogram.fsm.state import State, StatesGroup


class TasksSG(StatesGroup):
    main = State()
    task_1 = State()
    task_2 = State()
    task_3 = State()
