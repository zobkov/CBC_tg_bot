"""FSM states for the volunteer selection part 2 dialog."""

from aiogram.fsm.state import State, StatesGroup


class VolSelPart2SG(StatesGroup):
    # Entry / guard
    MAIN = State()

    # Intro screens
    intro = State()          # congratulations + explanation
    timer_warning = State()  # 35-minute timer info + ready/not-ready prompt

    # Written questions
    q1 = State()  # КБК ordinal (buttons 1ый–5ый)
    q2 = State()  # КБК date (text)
    q3 = State()  # КБК theme (text)
    q4 = State()  # Team experience (long text)
    q5 = State()  # Badge case (long text)
    q6 = State()  # Foreign guest case (long text)
    q7 = State()  # Want to give tours? (Yes/No buttons)

    # Optional branch – tour experience
    q7_experience = State()  # Has tour experience? (Yes/No buttons)
    q7_route = State()       # Tour route description (long text)

    # Video interview
    video_intro = State()  # Transition screen before video questions
    vq1 = State()          # Video question 1
    vq2 = State()          # Video question 2
    vq3 = State()          # Video question 3

    # Terminal
    success = State()
