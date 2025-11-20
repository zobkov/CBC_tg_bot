from __future__ import annotations

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Format, Multi
from magic_filter import F

from app.bot.states.feedback import FeedbackSG
from .getters import get_tasks_feedback, get_interview_feedback


tasks_feedback_dialog = Dialog(
    Window(
        Multi(
            Const("📝 <b>Обратная связь – Тестовое задание</b>\n"),
            Format("{task_feedback_text}"),
            sep="\n"
        ),
        Cancel(Const("🏠 Главное меню"), id="tasks_feedback_close"),
        state=FeedbackSG.feedback_menu,
        getter=get_tasks_feedback,
        when="has_task_feedback",
    ),
    Window(
        Const("⚠️ Обратная связь по тестовым заданиям недоступна."),
        Cancel(Const("🏠 Главное меню"), id="tasks_feedback_close_missing"),
        state=FeedbackSG.feedback_menu,
        getter=get_tasks_feedback,
        when=~F["has_task_feedback"],
    ),
)


interview_feedback_dialog = Dialog(
    Window(
        Multi(
            Const("🎦 <b>Обратная связь – Собеседование</b>\n"),
            Format("{interview_feedback_text}"),
            sep="\n"
        ),
        Cancel(Const("🏠 Главное меню"), id="interview_feedback_close"),
        state=FeedbackSG.interview_feedback,
        getter=get_interview_feedback,
        when="has_interview_feedback",
    ),
    Window(
        Const("⚠️ Обратная связь по собеседованию недоступна."),
        Cancel(Const("🏠 Главное меню"), id="interview_feedback_close_missing"),
        state=FeedbackSG.interview_feedback,
        getter=get_interview_feedback,
        when=~F["has_interview_feedback"],
    ),
)
