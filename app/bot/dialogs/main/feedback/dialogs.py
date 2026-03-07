"""Dialog definitions for the guest feedback flow."""

from __future__ import annotations

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Select
from aiogram_dialog.widgets.text import Const, Format, Multi
from magic_filter import F

from app.bot.dialogs.legacy.states.feedback import FeedbackSG
from .getters import (
    get_tasks_feedback_menu,
    get_task_feedback_details,
    get_interview_feedback,
)
from .handlers import on_task_selected, on_back_to_tasks


feedback_dialog = Dialog(
    Window(
        Multi(
            Const("📝 <b>Обратная связь – Тестовое задание</b>\n"),
            Const(
                "Выбери задание, чтобы посмотреть комментарии.",
                when=F["has_task_feedback"],
            ),
            Const(
                "⚠️ Обратная связь по тестовым заданиям недоступна.",
                when=~F["has_task_feedback"],
            ),
            sep="\n",
        ),
        Group(
            Select(
                Format("📋 {item[title]}"),
                id="task_feedback_select",
                items="tasks",
                item_id_getter=lambda item: item["task_id"],
                on_click=on_task_selected,
                when=F["has_task_feedback"],
            ),
            width=1,
        ),
        Cancel(Const("🏠 Главное меню"), id="tasks_feedback_close"),
        state=FeedbackSG.feedback_menu,
        getter=get_tasks_feedback_menu,
    ),
    Window(
        Multi(
            Const("📝 <b>Обратная связь – Тестовое задание</b>\n"),
            Format("<b>{task_title}</b>\n"),
            Format("{task_feedback_text}"),
            sep="\n"
        ),
        Group(
            Button(
                Const("↩️ Назад"),
                id="task_feedback_back",
                on_click=on_back_to_tasks,
            ),
            Cancel(
                Const("🏠 Главное меню"),
                id="tasks_feedback_close_from_details",
            ),
            width=1,
        ),
        state=FeedbackSG.show_feedback,
        getter=get_task_feedback_details,
    ),
    Window(
        Multi(
            Const("🎦 <b>Обратная связь – Собеседование</b>\n"),
            Format(
                "{interview_feedback_text}",
                when=F["has_interview_feedback"],
            ),
            Const(
                "⚠️ Обратная связь по собеседованию недоступна.",
                when=~F["has_interview_feedback"],
            ),
            sep="\n",
        ),
        Cancel(Const("🏠 Главное меню"), id="interview_feedback_close"),
        state=FeedbackSG.interview_feedback,
        getter=get_interview_feedback,
    ),
)
