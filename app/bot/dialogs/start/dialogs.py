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
        Format("Рады, что ты здесь! Сейчас расскажем об отборе немного подробнее. "),
        Start(
            Const("Далее"),
            state=MainMenuSG.main_menu,
            mode=StartMode.RESET_STACK,
            id="Start_main_menu_from_intro"
            ),
        state=StartSG.start,
    ),
)