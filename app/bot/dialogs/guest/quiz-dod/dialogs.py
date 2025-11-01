"""
Диалог квиза на день открытых дверей
"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Row, Back, Start, SwitchTo, Next
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia
from aiogram_dialog.widgets.input import TextInput

from .getters import *
from .states import QuizDodSG
from .handlers import (
    name_error_handler,
    email_error_handler,
    phone_error_handler,
    name_check,
    email_check,
    phone_check
)
from app.bot.states.feedback import FeedbackSG


quiz_dod_dialog = Dialog(
    # Главное меню квиза
    Window(
        Const("""大家好! Мы подготовили короткий квиз, чтобы проверить, насколько хорошо ты знаешь культуру и традиции Поднебесной, и познакомить тебя с нашим проектом.

И это только начало  👀 

Совсем скоро — лекции от экспертов, новые челленджи, онлайн-встречи с ребятами из разных регионов и другие сюрпризы от команды КБК! 

Подписывайся на наши соцсети — впереди ещё много всего интересного! 

Не тяни — жми «начать квиз» и вперёд 🚀"""),
        SwitchTo(),
        state=QuizDodSG.MAIN,
    ),

    # Начальная анкета

    # name
    Window(
        Const("Введи свое имя и фамилию:"),
        TextInput(
            id="Q_DOD_name",
            on_error=name_error_handler,
            on_success=Next(),
            type_factory=name_check,
        ),
    ),
    # telephone
    Window(
        Const("Введи свой номер телефона:"),
        TextInput(
            id="Q_DOD_phone",
            on_error=phone_error_handler,
            on_success=Next(),
            type_factory=phone_check,
        ),
    ),
    # e-mail
    Window(
        Const("Введи свою электронную почту:"),
        TextInput(
            id="Q_DOD_email",
            on_error=email_error_handler,
            on_success=Next(),
            type_factory=email_check,
        ),
    ),

)