"""Guest dialog window definitions."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Start, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.guest import getters as guest_getters
from app.bot.dialogs.guest.handlers import on_grants_clicked
from app.bot.dialogs.guest.quiz_dod.states import QuizDodSG
from app.bot.dialogs.online.states import OnlineSG
from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.selections.creative.part_2.states import CreativeSelectionPart2SG
from app.bot.dialogs.settings.states import SettingsSG

_MAIN_MENU_TEXT = """🏠 <b>Личный кабинет участника КБК'26</b>


Здесь ты можешь найти всю актуальную информацию о проекте! Совсем скоро мы начнём добавлять новые форматы, поэтому <b>подписывайся на наши медиа</b>, чтобы ничего не пропустить!


<b>Актуальные события:</b>
• Идёт регистрация на <b>конкурс Росмолодёжь.Гранты</b> — заявки принимаются до 03.04.26, 10:00 МСК

 
"""


guest_menu_dialog = Dialog(
    Window(
        DynamicMedia("media"),
        Format(_MAIN_MENU_TEXT),
        Row(
            Start(
                Const("🎭 Кастинг"),
                id="casting_creative_button",
                state=CreativeSelectionPart2SG.MAIN,
                when="show_casting",
            ),
        ),
        Row(
            Start(
                Const("📗 Онлайн-мероприятия"),
                id="online_button",
                state=OnlineSG.MAIN,
            ),
            when="is_admin",
        ),
        Row(
            Button(
                Const("🏆 Росмолодёжь.Гранты"),
                id="grants_btn",
                on_click=on_grants_clicked,
            ),
            when="is_admin",
        ),
        Row(
            Start(
                Const("⚙️ Помощь и настройки"),
                id="settings",
                state=SettingsSG.MAIN,
            ),
            Url(Const("Наши медиа"), Const("https://taplink.cc/forumcbc?from=tgbot"), id="url_to_taplink")
        ),
        state=GuestMenuSG.MAIN,
        getter=[
            guest_getters.get_main_menu_media,
            guest_getters.get_is_admin,
        ],
    ),
)
