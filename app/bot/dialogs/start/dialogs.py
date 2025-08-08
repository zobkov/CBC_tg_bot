from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Radio, Row, ScrollingGroup, Next, Cancel, Back, Start, Group, Column
from aiogram_dialog.widgets.text import Format, Const

from app.bot.states.start import StartSG
from app.bot.states.main_menu import MainMenuSG

from aiogram_dialog import DialogManager, StartMode
from aiogram.types import ContentType
from aiogram_dialog.widgets.media import StaticMedia

start_dialog = Dialog(
    Window(
        StaticMedia(
            url="https://www.regberry.ru/sites/default/files/og-image/kbk-2025.jpg",
            type=ContentType.PHOTO,
        ),
        Format("Привет! Мы команда КБК 2026. Мы будем рады видеть тебя у нас) Тут классссс"),
        Next(),
        state=StartSG.start,
    ),
    Window(
        StaticMedia(
            url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR8AcP5ERLyfAAQpLY0qn9sVEh6Z_g5X4BVoQ&s",
            type=ContentType.PHOTO,
        ),
        Format("Тут мы продолжаем рассказывать о нас че кого куда и как. Делаем это текстом или каруселькой"),
        Next(),
        state=StartSG.start_2,
    ),
    Window(
        StaticMedia(
            url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR8AcP5ERLyfAAQpLY0qn9sVEh6Z_g5X4BVoQ&s",
            type=ContentType.PHOTO,
        ),
        Format("Если мы тебя зинтересовали – кликай скорее на кнопку!!!!"),
        Start(
            Const("REGISTER"),
            state=MainMenuSG.main_menu,
            mode=StartMode.RESET_STACK,
            id="Start_main_menu_from_intro"
            ),
        state=StartSG.start_3,
    ),
)