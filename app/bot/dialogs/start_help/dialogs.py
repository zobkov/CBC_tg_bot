"""Aiogram-dialog windows for the start_help onboarding flow."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo, Url
from aiogram_dialog.widgets.text import Const

from app.bot.dialogs.start_help.states import StartHelpSG
from app.bot.dialogs.start_help.handlers import (
    on_yes_clicked,
    on_no_clicked,
    on_has_reg_yes,
    on_has_reg_no,
    on_has_code_clicked,
    code_check,
    code_error_handler,
    on_code_entered,
)

_WANT_REG_TEXT = """<b>Привет!</b> 

Ты в официальном боте КБК — это твой главный помощник для участия в форуме КБК и всех наших проектах. Здесь ты можешь следить за анонсами лекций и событий и получать море другой полезной информации.

Если тебе интересно познавать Китай не по учебникам, то самое время присоединиться к КБК!

<b>Ты хочешь зарегестрироваться на Форум КБК’26?</b>
<i>Если ты хочешь пройти отбор волонтеров, или зарегестрироваться позже, то нажимай «Нет» или /menu</i>"""

_SITE_REG_TEXT = "Проходил ли ты регистрацию на сайте?"

_NEED_REG_TEXT = (
    "Чтобы пользоваться ботом, необходимо пройти регистрацию на сайте.\n\n"
    "Переходи по ссылке и заполни форму. Потом тебе выдадут ссылку на бота — "
    "возвращайся по ней, чтобы закончить регистрацию! Или вводи полученный код.\n\n"
    "Контакты:\n"
    "Общие вопросы: @cbc_assistant\n"
    "Тех. поддержка: @zobko"
)

_ID_ENTER_TEXT = "Введи свой уникальный код, полученный после регистрации на сайте."

_WRONG_CODE_TEXT = (
    "Код неверный или мы не смогли найти его 😢\n\n"
    "Попробуй ещё раз ввести код или пройти регистрацию.\n\n"
    "Если проблема сохраняется, мы всегда на связи!\n"
    "Тех. поддержка: @zobko"
)

start_help_dialog = Dialog(
    # ── 1. want_reg ──────────────────────────────────────────────────────────
    Window(
        Const(_WANT_REG_TEXT),
        Row(
            Button(Const("Да"), id="sh_yes", on_click=on_yes_clicked),
            Button(Const("Нет"), id="sh_no", on_click=on_no_clicked),
        ),
        state=StartHelpSG.want_reg,
    ),

    # ── 2. site_reg ───────────────────────────────────────────────────────────
    Window(
        Const(_SITE_REG_TEXT),
        Row(
            Button(Const("Да"), id="sh_has_reg_yes", on_click=on_has_reg_yes),
            Button(Const("Нет"), id="sh_has_reg_no", on_click=on_has_reg_no),
        ),
        state=StartHelpSG.site_reg,
    ),

    # ── 3. need_reg ───────────────────────────────────────────────────────────
    Window(
        Const(_NEED_REG_TEXT),
        Url(
            Const("Регистрация на сайте"),
            Const("https://forum-cbc.ru/registration.html"),
            id="sh_reg_url",
        ),
        Button(
            Const("У меня уже есть код"),
            id="sh_has_code",
            on_click=on_has_code_clicked,
        ),
        state=StartHelpSG.need_reg,
    ),

    # ── 4. id_enter ───────────────────────────────────────────────────────────
    Window(
        Const(_ID_ENTER_TEXT),
        TextInput(
            id="sh_code_input",
            type_factory=code_check,
            on_error=code_error_handler,
            on_success=on_code_entered,
        ),
        SwitchTo(
            Const("Назад к регистрации"),
            id="sh_back_to_need_reg",
            state=StartHelpSG.need_reg,
        ),
        state=StartHelpSG.id_enter,
    ),

    # ── 5. wrong_code ─────────────────────────────────────────────────────────
    Window(
        Const(_WRONG_CODE_TEXT),
        TextInput(
            id="sh_code_retry_input",
            type_factory=code_check,
            on_error=code_error_handler,
            on_success=on_code_entered,
        ),
        SwitchTo(
            Const("Назад к регистрации"),
            id="sh_back_to_need_reg_from_wrong",
            state=StartHelpSG.need_reg,
        ),
        state=StartHelpSG.wrong_code,
    ),
)
