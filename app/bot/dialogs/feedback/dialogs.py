"""
Feedback dialog
"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button, Group, Select, Start, Back
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from magic_filter import F

from app.bot.states.feedback import FeedbackSG
from app.bot.states.main_menu import MainMenuSG
from .getters import (
    get_user_feedback_positions,
    get_selected_feedback
)
from .handlers import (
    on_feedback_position_selected,
    on_back_to_feedback_menu,
    on_back_to_main_menu
)


feedback_dialog = Dialog(
    # Feedback menu with available positions
    Window(
        Multi(
            Const("📝 <b>Обратная связь</b>\n"),
            Const("Мы подготовили персональную обратную связь по твоему тестовому заданию. Руководители внимательно изучили решения, чтобы каждый участник увидел свои сильные стороны и точки роста. Выбери направление, по которому хочешь получить обратную связь 👇\n", when="has_feedback"),
            Const("❌ Обратная связь отсутствует", when=~F["has_feedback"]),
            sep="\n"
        ),
        Group(
            Select(
                Format("📋 {item[full_title]}"),
                items="feedback_positions",
                id="feedback_position_select",
                item_id_getter=lambda item: f"fb_pos_{item['priority']}",
                on_click=on_feedback_position_selected,
                when="has_feedback"
            ),
            width=1
        ),
        Start(
            Const("🏠 Главное меню"),
            id="main_menu",
            state=MainMenuSG.main_menu
        ),
        state=FeedbackSG.feedback_menu,
        getter=get_user_feedback_positions,
    ),
    
    # Show specific feedback
    Window(
        Multi(
            Const("📝 <b>Обратная связь</b>\n"),
            Format("<b>Позиция:</b> {position_info[full_title]}\n"),
            Format("<b>Комментарий:</b>\n{feedback_text}"),
            sep="\n"
        ),
        Group(
            Button(
                Const("↩️ Назад к списку"),
                id="back_to_feedback_menu",
                on_click=on_back_to_feedback_menu
            ),
            Start(
                Const("🏠 Главное меню"),
                id="main_menu_from_feedback",
                state=MainMenuSG.main_menu
            ),
            width=1
        ),
        state=FeedbackSG.show_feedback,
        getter=get_selected_feedback,
    )
)