from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Start, SwitchTo
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import StaticMedia, DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType


from app.utils.optimized_dialog_widgets import get_file_id_for_path
from app.bot.states.main_menu import MainMenuSG
from app.bot.states.first_stage import FirstStageSG
from .getters import get_current_stage_info, get_application_status, get_support_contacts, get_main_menu_media
from .handlers import on_current_stage_clicked, on_support_clicked

main_menu_dialog = Dialog(
    Window(
        DynamicMedia(
            "media"
        ),
        Format("🏠 <b>Личный кабинет кандидата в команду КБК 2026</b>\n\n"
               "📅 <b>Текущий этап:</b> {stage_name}\n"
               "📍 <b>Статус заявки:</b> {status_text}\n\n"
               "⏰ Дедлайн: 28.09.2025, 23:59"
               "{deadline_info}\n"
               "{stage_description}"),
        Row(
            Button(
                Const("📋 Тестовые задания"),
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
        getter=[get_current_stage_info, get_application_status, get_main_menu_media]
    ),
    Window(
        StaticMedia(
            path="app/bot/assets/images/support/support.png"
        ),
        Format("📞 <b>Поддержка</b>\n\n"
               "Если возникнут вопросы, мы всегда на связи! Ты можешь обратиться к одному из контактов ниже и задать все интересующие тебя вопросы.\n\n"
               "<b>По общим вопросам:</b> {general_support}\n"
               "<b>Техническая поддержка:</b> {technical_support}\n"
               ),
        Back(Const("◀️ Назад")),
        state=MainMenuSG.support,
        getter=get_support_contacts
    ),
    Window(
        Format("📞 <b>Тут скоро будут тестовые задания</b>\n\nМы почти готовы рассылать тестовые задания. Если ты прошел первый этап отбора, то возвращайся в бота завтра, чтобы забрать файлы для своих заданий!\n\n"),
        SwitchTo(Const("◀️ Назад"), state=MainMenuSG.main_menu, id="to_main_menu_from_bot_aval"),
        state=MainMenuSG.not_availabe,
        getter=get_support_contacts
    ),
)