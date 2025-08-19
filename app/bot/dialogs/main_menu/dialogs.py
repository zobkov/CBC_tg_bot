from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Start
from aiogram_dialog.widgets.text import Format, Const

from app.bot.states.main_menu import MainMenuSG
from app.bot.states.first_stage import FirstStageSG
from .getters import get_current_stage_info, get_application_status, get_support_contacts
from .handlers import on_current_stage_clicked, on_support_clicked

main_menu_dialog = Dialog(
    Window(
        Format("🏠 <b>Личный кабинет кандидата в команду КБК 2026</b>\n\n"
               "📅 <b>Текущий этап:</b> {stage_name}\n"
               "📝 <b>Статус заявки:</b> {status_text}\n\n"
               "{deadline_info}\n\n"
               "{stage_description}"),
        Row(
            Button(
                Const("📋 Текущий этап отбора"),
                id="current_stage",
                on_click=on_current_stage_clicked
            ),
        ),
        Row(
            Button(
                Const("📞 Поддержка"),
                id="support",
                on_click=on_support_clicked
            ),
        ),
        state=MainMenuSG.main_menu,
        getter=[get_current_stage_info, get_application_status]
    ),
    Window(
        Format("📞 <b>Поддержка</b>\n\n"
               "По общим вопросам: {general_support}\n"
               "Техническая поддержка: {technical_support}\n"
               ),
        Back(Const("◀️ Назад")),
        state=MainMenuSG.support,
        getter=get_support_contacts
    ),
)