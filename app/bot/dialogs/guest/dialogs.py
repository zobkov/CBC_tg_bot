"""
Диалог главного меню для гостей
"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Start, SwitchTo
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import StaticMedia, DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType


from app.utils.optimized_dialog_widgets import get_file_id_for_path


from app.bot.states.interview import InterviewSG
from app.bot.states.feedback import FeedbackSG
from .getters import get_current_stage_info, get_application_status, get_support_contacts, get_main_menu_media, get_task_button_info, get_interview_button_info, get_feedback_button_info, get_interview_datetime_info, get_interview_feedback
from .handlers import on_current_stage_clicked, on_support_clicked, on_interview_button_clicked
from .states import GuestMenuSG


guest_menu_dialog = Dialog(
    Window(
        DynamicMedia(
            "media"
        ),
        Format("""🏠 <b>Личный кабинет участника КБК'26</b>
               
Мы закончили основой отбор в команду. Спасибо всем за участие!
               """
        ),
        Row(
            Start(
                Const("📝 Получить обратную связь – Тестовое задание"),
                id="feedback_button",
                state=FeedbackSG.feedback_menu,
            ),
        ),
        Row(
            Start(
                Const("🎦 Получить обратную связь – Собеседование"),
                id="feedback_interview_button",
                state=GuestMenuSG.interview_feedback,
                when="has_interview_feedback",
            ),
        ),
        Row(
            SwitchTo(
                Const("📞 Поддержка"),
                id="support",
                state=GuestMenuSG.support
            ),
        ),
        state=GuestMenuSG.MAIN,
        getter=[get_current_stage_info, get_application_status, get_main_menu_media, get_task_button_info, get_interview_button_info, get_feedback_button_info, get_interview_datetime_info, get_interview_feedback]
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
        state=GuestMenuSG.support,
        getter=get_support_contacts
    ),
    Window(
        Format("🎦 <b>Обратная связь по собеседованию</b>\n\n"
               "{interview_feedback}"
               ),
        Back(Const("◀️ Назад")),
        state=GuestMenuSG.interview_feedback,
        getter=get_interview_feedback
    ),
)