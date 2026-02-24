"""
Диалог онлайн-лекций
"""

import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Row, Start, SwitchTo, Cancel, Group, Select, Button
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import DynamicMedia

from .getters import (
    get_schedule_list,
    get_event_details,
    get_my_events,
    get_my_event_detail,
    get_successful_registration_text,
    get_ics_file,
)
from .handlers import (
    on_event_selected,
    on_my_event_selected,
    on_register_clicked,
    on_cancel_registration_clicked,
    on_get_link_clicked,
)
from .states import OnlineSG

# Импортируем QuizDodSG для кнопки перехода к квизу
try:
    from app.bot.dialogs.guest.quiz_dod.states import QuizDodSG
except ImportError:
    QuizDodSG = None


_MAIN_MENU_TEXT = """
<b>📚 Онлайн-лекции</b>

Добро пожаловать в раздел онлайн-лекций КБК!

"""

_SCHEDULE_HEADER = "<b>🗓️ Расписание лекций</b>\n\n─────────────────"
_MY_EVENTS_HEADER = "<b>📚 Мои лекции</b>\n\n─────────────────"

_SUPPORT_TEXT = """
<b>❓ Помощь и поддержка</b>

Если у тебя возникли вопросы по онлайн-лекциям, обратись к координаторам отдела Амбассадоров.

📧 Контакты для связи:
• Telegram: @cbc_assistant

Часто задаваемые вопросы:

<b>Q: Когда становится доступна ссылка на трансляцию?</b>
A: Ссылка появляется в карточке лекции за 1 час до начала.

<b>Q: Нужно ли регистрироваться заранее?</b>
A: Да, регистрация помогает нам понять интерес к теме и отправить тебе напоминание.

<b>Q: Что делать, если я не смогу присутствовать?</b>
A: Ты можешь отменить регистрацию в любой момент в разделе "Мои лекции".
"""

_CALENDAR_HELP = """📅 <b>Добавить событие в календарь</b>

Для удобства мы подготовили файл календаря (.ics) для этой лекции.

<b>Как использовать:</b>
1️⃣ Нажми на прикрепленный файл
2️⃣ Выбери приложение календаря на твоем устройстве
3️⃣ Событие автоматически добавится в календарь

Если событие добавить не получилось, то обратись к <a href="https://docs.google.com/document/d/1P5V90jIe4LKvU1h7U7EEXPOluCixv_2fKhyLVSsaSpQ/edit?usp=sharing">гайду</a>
"""

online_dialog = Dialog(
    # =============
    # MAIN - Главное меню
    # =============
    Window(
        Const(_MAIN_MENU_TEXT),
        SwitchTo(
            Const("📆 Расписание лекций"),
            id="btn_schedule",
            state=OnlineSG.SCHEDULE,
        ),
        SwitchTo(
            Const("📚 Мои лекции"),
            id="btn_my_events",
            state=OnlineSG.MY_EVENTS,
        ),
        Row(
            SwitchTo(
                Const("❓ Помощь"),
                id="btn_support",
                state=OnlineSG.SUPPORT,
            ),
            Cancel(Const("⬅️ Назад")),
        ),
        state=OnlineSG.MAIN,
    ),

    # =============
    # SCHEDULE - Расписание лекций
    # =============
    Window(
        Const(_SCHEDULE_HEADER),
        Format("{schedule_text}"),
        Group(
            Select(
                Format("{item[0]}"),
                id="event_selection",
                items="events",
                item_id_getter=operator.itemgetter(1),
                on_click=on_event_selected,
            ),
            width=1,
        ),
        Back(Const("⬅️ Назад")),
        getter=get_schedule_list,
        state=OnlineSG.SCHEDULE,
    ),

    # =============
    # SCHEDULE_EVENT - Детали лекции из расписания
    # =============
    Window(
        Format("{event_details}"),
        # Кнопка регистрации/отмены (взаимоисключающие условия)
        Button(
            Const("✅ Зарегистрироваться"),
            id="btn_register",
            on_click=on_register_clicked,
            when=lambda data, widget, manager: not data.get("is_registered", False),
        ),
        Button(
            Const("❌ Отменить регистрацию"),
            id="btn_cancel_reg",
            on_click=on_cancel_registration_clicked,
            when="is_registered",
        ),
        SwitchTo(
            Const("📅 Добавить в календарь"),
            id="btn_add_to_calendar",
            state=OnlineSG.CALENDAR_ADDITION_1,
            when="is_registered",
        ),
        Back(Const("⬅️ Назад")),
        getter=get_event_details,
        state=OnlineSG.SCHEDULE_EVENT,
    ),

    # =============
    # CALENDAR_ADDITION_1 - from schedule
    # =============
    Window(
        Const(_CALENDAR_HELP),
        DynamicMedia("ics_file"),
        Back(Const("⬅️ Назад")),
        getter=get_ics_file,
        state=OnlineSG.CALENDAR_ADDITION_1,
    ),

    # =============
    # MY_EVENTS - Мои зарегистрированные лекции
    # =============
    Window(
        Const(_MY_EVENTS_HEADER),
        Format("{my_events_text}"),
        Group(
            Select(
                Format("{item[0]}"),
                id="my_event_selection",
                items="my_events",
                item_id_getter=operator.itemgetter(1),
                on_click=on_my_event_selected,
            ),
            width=1,
        ),
        SwitchTo(Const("⬅️ Назад"), id="my_to_main", state=OnlineSG.MAIN),
        getter=get_my_events,
        state=OnlineSG.MY_EVENTS,
    ),

    # =============
    # MY_EVENT_DETAIL - Детали моей лекции
    # =============
    Window(
        Format("{my_event_details}"),
        Button(
            Const("🔗 Получить ссылку"),
            id="btn_get_link",
            on_click=on_get_link_clicked,
        ),
        SwitchTo(
            Const("📅 Добавить в календарь"),
            id="btn_add_to_calendar_my",
            state=OnlineSG.CALENDAR_ADDITION,
        ),
        Button(
            Const("❌ Отменить регистрацию"),
            id="btn_cancel_my_reg",
            on_click=on_cancel_registration_clicked,
        ),
        Back(Const("⬅️ Назад")),
        getter=get_my_event_detail,
        state=OnlineSG.MY_EVENT_DETAIL,
    ),

    # =============
    # CALENDAR_ADDITION - Добавление в календарь
    # =============
    Window(
        Const(_CALENDAR_HELP),
        DynamicMedia("ics_file"),
        Back(Const("⬅️ Назад")),
        getter=get_ics_file,
        state=OnlineSG.CALENDAR_ADDITION,
    ),

    # =============
    # SUCCESSFUL_REGISTRATION - Успешная регистрация
    # =============
    Window(
        Format("{success_text}"),
        SwitchTo(
            Const("🗓️ Добавить в календарь"),
            id="btn_add_to_calendar_success",
            state=OnlineSG.CALENDAR_ADDITION_1,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="btn_back_to_main",
            state=OnlineSG.SCHEDULE,
        ),
        getter=get_successful_registration_text,
        state=OnlineSG.SUCCESSFUL_REGISTRATION,
    ),

    # =============
    # SUPPORT - Помощь
    # =============
    Window(
        Const(_SUPPORT_TEXT),
        SwitchTo(Const("⬅️ Назад"), id="support_to_main", state=OnlineSG.MAIN),
        state=OnlineSG.SUPPORT,
    ),

    
)
