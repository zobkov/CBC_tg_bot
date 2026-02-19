"""Registration dialog window definitions."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from app.bot.dialogs.registration.states import RegistrationSG
from app.bot.dialogs.registration.handlers import (
    name_check,
    name_error_handler,
    on_name_entered,
    university_check,
    university_error_handler,
    on_university_entered,
    email_check,
    email_error_handler,
    on_email_entered,
    on_start_registration,
)


_WELCOME_TEXT = (
    "您好！<b>Добро пожаловать в бота Всероссийского проекта «Китай Бизнес Культура»!</b>\n\n"
    "Для начала работы нам нужно узнать о тебе немного больше."
)

_NAME_PROMPT = (
    "<b>Как тебя зовут?</b>\n\n"
    "Напиши свою фамилию, имя и отчество полностью."
)

_UNIVERSITY_PROMPT = (
    "<b>Укажи данные о твоем обучении.</b>\n\n"
    "Напиши, пожалуйста, в формате: <i>Университет, факультет, курс, год выпуска</i>\n\n"
    "Например: СПбГУ, Юрфак, 3, 2027"
)

_EMAIL_PROMPT = (
    "<b>Электронная почта</b>\n\n"
    "Укажи действующий e-mail."
)


registration_dialog = Dialog(
    Window(
        Const(_WELCOME_TEXT),
        Button(
            Const("📝 Начать регистрацию"),
            id="start_registration",
            on_click=on_start_registration,
        ),
        state=RegistrationSG.MAIN,
    ),
    Window(
        Const(_NAME_PROMPT),
        TextInput(
            id="reg_name",
            on_error=name_error_handler,
            on_success=on_name_entered,
            type_factory=name_check,
        ),
        state=RegistrationSG.name,
    ),
    Window(
        Const(_UNIVERSITY_PROMPT),
        TextInput(
            id="reg_university",
            on_error=university_error_handler,
            on_success=on_university_entered,
            type_factory=university_check,
        ),
        state=RegistrationSG.university,
    ),
    Window(
        Const(_EMAIL_PROMPT),
        TextInput(
            id="reg_email",
            on_error=email_error_handler,
            on_success=on_email_entered,
            type_factory=email_check,
        ),
        state=RegistrationSG.email,
    ),
)
