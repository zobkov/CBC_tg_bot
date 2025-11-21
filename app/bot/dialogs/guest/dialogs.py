"""Guest dialog window definitions."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Row, Start, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.guest import getters as guest_getters
from app.bot.dialogs.guest.quiz_dod.states import QuizDodSG
from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.states.feedback import FeedbackSG

_MAIN_MENU_TEXT = (
    "🏠 <b>Личный кабинет участника КБК'26</b>\n\n"
    "Здесь ты можешь найти всю актуальную информацию о проекте! Совсем скоро мы "
    "начнём добавлять новые форматы, поэтому подписывайся на наши медиа, чтобы "
    "ничего не пропустить:\n"
    "<a href=\"https://t.me/forumcbc\">Мы в ТГ</a>\n"
    "<a href=\"https://vk.com/forumcbc\">Мы в ВК</a>"
)

_SUPPORT_TEXT = (
    "📞 <b>Поддержка</b>\n\n"
    "Если возникнут вопросы, мы всегда на связи! Ты можешь обратиться к одному "
    "из контактов ниже и задать все интересующие тебя вопросы.\n\n"
    "<b>По общим вопросам:</b> {general_support}\n"
    "<b>Техническая поддержка:</b> {technical_support}\n\n"
    "Частые вопросы: "
    "https://docs.google.com/document/d/1fV2IA_k5eY3TSM4Xue1sYR1OS8-AkHDGN_t4ub"
    "KNMlA/edit?usp=sharing"
)


guest_menu_dialog = Dialog(
    Window(
        DynamicMedia("media"),
        Format(_MAIN_MENU_TEXT),
        Row(
            Start(
                Const("📝 Обратная связь – Тестовое задание"),
                id="feedback_button",
                state=FeedbackSG.feedback_menu,
            ),
        ),
        Row(
            Start(
                Const("🎦 Обратная связь – Собеседование"),
                id="feedback_interview_button",
                state=FeedbackSG.interview_feedback,
                when="has_interview_feedback",
            ),
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
                state=GuestMenuSG.support,
            ),
        ),
        state=GuestMenuSG.MAIN,
        getter=[
            guest_getters.get_current_stage_info,
            guest_getters.get_application_status,
            guest_getters.get_main_menu_media,
            guest_getters.get_task_button_info,
            guest_getters.get_interview_button_info,
            guest_getters.get_feedback_button_info,
            guest_getters.get_interview_datetime_info,
            guest_getters.get_interview_feedback,
        ],
    ),
    Window(
        StaticMedia(path="app/bot/assets/images/support/support.png"),
        Format(_SUPPORT_TEXT),
        Back(Const("◀️ Назад")),
        state=GuestMenuSG.support,
        getter=guest_getters.get_support_contacts,
    ),
)
