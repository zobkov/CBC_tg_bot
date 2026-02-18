"""Guest dialog window definitions."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Row, Start
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.guest import getters as guest_getters
from app.bot.dialogs.guest.quiz_dod.states import QuizDodSG
from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.selections.creative.states import CreativeSelectionSG
from app.bot.dialogs.settings.states import SettingsSG

_MAIN_MENU_TEXT = (
    "🏠 <b>Личный кабинет участника КБК'26</b>\n\n"
    "Здесь ты можешь найти всю актуальную информацию о проекте! Совсем скоро мы "
    "начнём добавлять новые форматы, поэтому подписывайся на наши медиа, чтобы "
    "ничего не пропустить:\n\n"
    "<a href=\"https://t.me/forumcbc\">Мы в ТГ</a>\n"
    "<a href=\"https://vk.com/forumcbc\">Мы в ВК</a>\n"
    "<a href=\"https://forum-cbc.ru\">Наш сайт</a>"
)


guest_menu_dialog = Dialog(
    Window(
        DynamicMedia("media"),
        Format(_MAIN_MENU_TEXT),
        Row(
            Start(
                Const("🎯 Квиз КБК"),
                id="quiz_dod_button",
                state=QuizDodSG.MAIN,
            ),
        ),
        Row(
            Start(
                Const("🎭 Кастинг"),
                id="casting_creative_button",
                state=CreativeSelectionSG.MAIN,
            ),
        ),
        Row(
            Start(
                Const("⚙️ Настройки"),
                id="settings",
                state=SettingsSG.MAIN,
            ),
        ),
        state=GuestMenuSG.MAIN,
        getter=[
            guest_getters.get_main_menu_media
        ],
    ),
)
