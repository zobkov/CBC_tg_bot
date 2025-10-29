from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Row, Back, SwitchTo
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia


from .states import StaffMenuSG

from .getters import get_current_stage_info, get_application_status, get_support_contacts, get_main_menu_media, get_task_button_info, get_interview_button_info, get_feedback_button_info, get_interview_datetime_info


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
            SwitchTo(
                Const("📞 Поддержка"),
                id="support",
                state=StaffMenuSG.support,
            ),
        ),
        state=StaffMenuSG.MAIN,
        getter=[get_current_stage_info, get_application_status, get_main_menu_media, get_task_button_info, get_interview_button_info, get_feedback_button_info, get_interview_datetime_info]
    ),
    Window(
        StaticMedia(
            path="app/bot/assets/images/support/support.png"
        ),
        Format("📞 <b>Поддержка</b>\n\n"
               "Если возникнут вопросы, мы всегда на связи! Ты можешь обратиться к одному из контактов ниже и задать все интересующие тебя вопросы.\n\n"
               "<b>По общим вопросам:</b> {general_support}\n"
               "<b>Техническая поддержка:</b> {technical_support}\n"
               "\nЧастые вопросы: https://docs.google.com/document/d/1fV2IA_k5eY3TSM4Xue1sYR1OS8-AkHDGN_t4ubKNMlA/edit?usp=sharing"
               ),
        Back(Const("◀️ Назад")),
        state=StaffMenuSG.support,
        getter=get_support_contacts
    ),
)