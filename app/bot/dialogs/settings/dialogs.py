"""Settings dialog window definitions."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Cancel, Row, Start, SwitchTo
from aiogram_dialog.widgets.media import StaticMedia, DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.broadcasts.states import BroadcastMenuSG
from app.bot.dialogs.settings.states import SettingsSG
from app.bot.dialogs.settings import getters as settings_getters
from app.bot.dialogs.settings import handlers as settings_handlers
from app.bot.dialogs.main import getters as main_getters


_SETTINGS_MAIN_TEXT = (
    "⚙️ <b>Настройки</b>\n\n"
)

_PROFILE_TEXT = (
    "👤 <b>Твой профиль</b>\n\n"
    "<b>ФИО:</b> {full_name}\n"
    "<b>Обучение:</b> {education}\n"
    "<b>Email:</b> {email}\n\n"
    "Выбери, что хочешь изменить:"
)

_SUPPORT_TEXT = (
    "📞 <b>Поддержка</b>\n\n"
    "Если возникнут вопросы, мы всегда на связи! Ты можешь обратиться к одному "
    "из контактов ниже и задать все интересующие тебя вопросы.\n\n"
    "<b>По общим вопросам:</b> {general_support}\n"
    "<b>Техническая поддержка:</b> {technical_support}\n\n"
)

_EDIT_NAME_PROMPT = (
    "✏️ <b>Изменить ФИО</b>\n\n"
    "Напиши свою фамилию, имя и отчество полностью."
)

_EDIT_EDUCATION_PROMPT = (
    "✏️ <b>Изменить информацию об обучении</b>\n\n"
    "Например: <i>Университет, факультет, курс, год выпуска</i>"
)

_EDIT_EMAIL_PROMPT = (
    "✏️ <b>Изменить email</b>\n\n"
    "Укажи действующий e-mail."
)


settings_dialog = Dialog(
    # Main settings menu
    Window(
        Const(_SETTINGS_MAIN_TEXT),
        Row(
            SwitchTo(
                Const("👤 Профиль"),
                id="profile",
                state=SettingsSG.PROFILE,
            ),
        ),
        Row(
            SwitchTo(
                Const("📞 Поддержка"),
                id="support",
                state=SettingsSG.SUPPORT,
            ),
            Start(
                Const("📬 Рассылки"),
                id="broadcasts",
                state=BroadcastMenuSG.MAIN,
            ),
        ),
        Cancel(Const("◀️ Назад")),
        state=SettingsSG.MAIN,
    ),
    
    # Profile view with edit buttons
    Window(
        Format(_PROFILE_TEXT),
        Row(
            SwitchTo(
                Const("✏️ Изменить ФИО"),
                id="edit_name",
                state=SettingsSG.edit_name,
            ),
        ),
        Row(
            SwitchTo(
                Const("✏️ Изменить обучение"),
                id="edit_education",
                state=SettingsSG.edit_education,
            ),
        ),
        Row(
            SwitchTo(
                Const("✏️ Изменить email"),
                id="edit_email",
                state=SettingsSG.edit_email,
            ),
        ),
        SwitchTo(Const("◀️ Назад"), id="back_to_menu", state=SettingsSG.MAIN),
        state=SettingsSG.PROFILE,
        getter=settings_getters.get_user_profile,
    ),
    
    # Support window
    Window(
        DynamicMedia("media"),
        Format(_SUPPORT_TEXT),
        SwitchTo(Const("◀️ Назад"), id="back_to_menu", state=SettingsSG.MAIN),
        state=SettingsSG.SUPPORT,
        getter=[settings_getters.get_support_contacts,settings_getters.get_support_media]
    ),
    
    # Edit name window
    Window(
        Const(_EDIT_NAME_PROMPT),
        TextInput(
            id="edit_name_input",
            on_error=settings_handlers.name_error_handler,
            on_success=settings_handlers.on_name_entered,
            type_factory=settings_handlers.name_check,
        ),
        SwitchTo(Const("❌ Отмена"), id="back_to_profile", state=SettingsSG.PROFILE),
        state=SettingsSG.edit_name,
    ),
    
    # Edit education window
    Window(
        Const(_EDIT_EDUCATION_PROMPT),
        TextInput(
            id="edit_education_input",
            on_error=settings_handlers.education_error_handler,
            on_success=settings_handlers.on_education_entered,
            type_factory=settings_handlers.education_check,
        ),
        SwitchTo(Const("❌ Отмена"), id="back_to_profile", state=SettingsSG.PROFILE),
        state=SettingsSG.edit_education,
    ),
    
    # Edit email window
    Window(
        Const(_EDIT_EMAIL_PROMPT),
        TextInput(
            id="edit_email_input",
            on_error=settings_handlers.email_error_handler,
            on_success=settings_handlers.on_email_entered,
            type_factory=settings_handlers.email_check,
        ),
        SwitchTo(Const("❌ Отмена"), id="back_to_profile", state=SettingsSG.PROFILE),
        state=SettingsSG.edit_email,
    ),
)
