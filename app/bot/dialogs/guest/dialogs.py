"""Guest dialog window definitions."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Row, Start, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.guest import getters as guest_getters
from app.bot.dialogs.guest.quiz_dod.states import QuizDodSG
from app.bot.dialogs.online.states import OnlineSG
from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.selections.creative.states import CreativeSelectionSG
from app.bot.dialogs.settings.states import SettingsSG

_MAIN_MENU_TEXT = (
    "🏠 <b>Личный кабинет участника КБК'26</b>\n\n\n"
    "Актуальные события:\n\n"
    "• <b>Творческие коллективы КБК'26 ищут тебя!</b>\nМы ищем тех, кто любит сцену, хочет выступать и готов создавать настроение форума. Актёрство и мастер-классы — если это твое, то скорее присоединяйся к нам!\n\n\n"
    "Здесь ты можешь найти всю актуальную информацию о проекте! Совсем скоро мы "
    "начнём добавлять новые форматы, поэтому <b>подписывайся на наши медиа</b>, чтобы "
    "ничего не пропустить:\n\n"
)


guest_menu_dialog = Dialog(
    Window(
        DynamicMedia("media"),
        Format(_MAIN_MENU_TEXT),
        Row(
            Start(
                Const("📗 Онлайн"),
                id="quiz_dod_button",
                state=OnlineSG.MAIN,
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
                Const("⚙️ Помощь и настройки"),
                id="settings",
                state=SettingsSG.MAIN,
            ),
            Url(Const("Медиа КБК"), Const("https://taplink.cc/forumcbc?from=tgbot"), id="url_to_taplink")
        ),
        state=GuestMenuSG.MAIN,
        getter=[
            guest_getters.get_main_menu_media
        ],
    ),
)
