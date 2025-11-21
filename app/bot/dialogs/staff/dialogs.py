"""Main dialog of staff branch"""
import logging

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Row, Back, SwitchTo, Start
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia

from app.bot.dialogs.guest.quiz_dod.states import QuizDodSG

from .states import StaffMenuSG

from .getters import (get_user_info,
                      get_main_menu_media, get_support_contacts)


logger = logging.getLogger(__name__)


staff_menu_dialog = Dialog(
    Window(
        DynamicMedia(
            "media"
        ),
        Format("""
🏠 <b>Личный кабинет участника команды КБК</b>\n\n
Пройди анкетирование:
🔗 https://forms.yandex.ru/cloud/68eeb01402848ff3fe9134ee
"""
        ),
        Row(
            Start(
                Const("🎯 Квиз КБК"),
                id="quiz_dod_button",
                state=QuizDodSG.MAIN,
            ),
        ),
        Row(
            SwitchTo(
                Const("📞 Поддержка"),
                id="support",
                state=StaffMenuSG.support,
            ),
        ),
        state=StaffMenuSG.MAIN,
        getter=[get_user_info, get_main_menu_media,
                get_support_contacts]
    ),
    Window(
        StaticMedia(
            path="app/bot/assets/images/support/support.png"
        ),
        Format("📞 <b>Поддержка</b>\n\n"
               "Если возникнут вопросы, мы всегда на связи! Ты можешь обратиться к одному из контактов ниже и задать все интересующие тебя вопросы.\n\n" # pylint: disable=line-too-long
               "<b>По общим вопросам:</b> {general_support}\n"
               "<b>Техническая поддержка:</b> {technical_support}\n"
               "\nЧастые вопросы: https://docs.google.com/document/d/1fV2IA_k5eY3TSM4Xue1sYR1OS8-AkHDGN_t4ubKNMlA/edit?usp=sharing" # pylint: disable=line-too-long
               ),
        Back(Const("◀️ Назад")),
        state=StaffMenuSG.support,
        getter=get_support_contacts
    ),
)
