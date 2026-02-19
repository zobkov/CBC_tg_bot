"""
Диалог онлайн-лекций
"""

import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Row, Start, SwitchTo, Cancel, Group, Select, Button
from aiogram_dialog.widgets.text import Const, Format, Case

from .getters import (
    get_schedule_list,
    get_event_details,
    get_my_events,
    get_my_event_detail,
    get_successful_registration_text,
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

Здесь ты можешь:
• Просматривать расписание предстоящих лекций
• Регистрироваться на интересующие мероприятия
• Отслеживать свои зарегистрированные лекции
• Получать ссылки на трансляции
"""

_SCHEDULE_HEADER = "<b>📅 Расписание лекций</b>\n\n"
_MY_EVENTS_HEADER = "<b>📚 Мои лекции</b>\n\n"

_SUPPORT_TEXT = """
<b>❓ Помощь и поддержка</b>

Если у тебя возникли вопросы по онлайн-лекциям, обратись к координаторам отдела Амбассадоров.

📧 Контакты для связи:
• Telegram: @support_kbk

Часто задаваемые вопросы:

<b>Q: Когда становится доступна ссылка на трансляцию?</b>
A: Ссылка появляется в карточке лекции за 1 час до начала.

<b>Q: Нужно ли регистрироваться заранее?</b>
A: Да, регистрация помогает нам понять интерес к теме и отправить тебе напоминание.

<b>Q: Что делать, если я не смогу присутствовать?</b>
A: Ты можешь отменить регистрацию в любой момент в разделе "Мои лекции".
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
        # Кнопка квиза (если доступен)
        Start(
            Const("🔍 Квиз"),
            id="btn_quiz",
            state=QuizDodSG.MAIN if QuizDodSG else None,
        ) if QuizDodSG else None,
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
            width=2,
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
        # Кнопка регистрации/отмены (условная)
        Case(
            {
                True: Button(
                    Const("❌ Отменить регистрацию"),
                    id="btn_cancel_reg",
                    on_click=on_cancel_registration_clicked,
                ),
                False: Button(
                    Const("✅ Зарегистрироваться"),
                    id="btn_register",
                    on_click=on_register_clicked,
                ),
            },
            selector="is_registered",
        ),
        Back(Const("⬅️ Назад")),
        getter=get_event_details,
        state=OnlineSG.SCHEDULE_EVENT,
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
            width=2,
        ),
        Back(Const("⬅️ Назад")),
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
        Back(Const("⬅️ Назад")),
        getter=get_my_event_detail,
        state=OnlineSG.MY_EVENT_DETAIL,
    ),

    # =============
    # SUCCESSFUL_REGISTRATION - Успешная регистрация
    # =============
    Window(
        Format("{success_text}"),
        SwitchTo(
            Const("⬅️ Назад"),
            id="btn_back_to_main",
            state=OnlineSG.MAIN,
        ),
        getter=get_successful_registration_text,
        state=OnlineSG.SUCCESSFUL_REGISTRATION,
    ),

    # =============
    # SUPPORT - Помощь
    # =============
    Window(
        Const(_SUPPORT_TEXT),
        Back(Const("⬅️ Назад")),
        state=OnlineSG.SUPPORT,
    ),
)
