from aiogram.fsm.state import State, StatesGroup


class FeedbackSG(StatesGroup):
    """Feedback dialog states"""
    # Общий экран обратной связи по тестовым заданиям
    feedback_menu = State()

    # Зарезервировано для устаревшего сценария показа по позициям
    show_feedback = State()

    # Экран обратной связи после интервью
    interview_feedback = State()