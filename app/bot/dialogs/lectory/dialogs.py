"""Dialog definition for the Лекторий (lecture schedule) section."""
import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Group, Row, Select, SwitchTo, Url
from aiogram_dialog.widgets.text import Const, Format

from .getters import get_event_detail, get_my_questions, get_schedule
from .handlers import on_event_selected, on_question_error, on_question_submitted, question_validator
from .states import LectorySG

_NO_TRACK_TEXT = (
    "📅 <b>Лекторий</b>\n\n"
    "Выбери трек, чтобы увидеть расписание мероприятий."
)

_NO_EVENTS_TEXT = (
    "📅 <b>Лекторий</b>\n\n"
    "Расписание мероприятий трека уточняется."
)

_ASK_QUESTION_TEXT = (
    "❓ <b>Задать вопрос</b>\n\n"
    "Напиши свой вопрос — он будет передан организаторам и ты получишь ответ здесь, в боте.\n\n"
    "Максимум 1000 символов."
)

lectory_dialog = Dialog(
    # -----------------------------------------------------------------------
    # SCHEDULE — full day schedule view
    # -----------------------------------------------------------------------
    Window(
        Format("{schedule_text}", when="has_events"),
        Const(_NO_TRACK_TEXT, when=lambda data, w, m: not data.get("has_track")),
        Const(_NO_EVENTS_TEXT, when="has_track_no_events"),
        Group(
            Select(
                Format("{item[0]}"),
                id="event_sel",
                items="events",
                item_id_getter=operator.itemgetter(1),
                on_click=on_event_selected,
            ),
            width=1,
            when="has_events",
        ),
        Cancel(Const("◀️ Назад")),
        getter=get_schedule,
        state=LectorySG.SCHEDULE,
    ),

    # -----------------------------------------------------------------------
    # EVENT_DETAIL — individual event info + Q&A buttons
    # -----------------------------------------------------------------------
    Window(
        Format(
            "📖 <b>{event_name}</b>\n\n"
            "🕐 {event_time}  |  🏛 Ауд. {event_auditorium}\n"
            "📋 Формат: {event_format}\n\n"
            "{event_description}",
            when="has_format",
        ),
        Format(
            "📖 <b>{event_name}</b>\n\n"
            "🕐 {event_time}  |  🏛 Ауд. {event_auditorium}\n\n"
            "{event_description}",
            when=lambda data, w, m: not data.get("has_format"),
        ),
        Const("✅ Вопрос отправлен!", when="question_submitted"),
        Url(
            Const("🔗 Трансляция"),
            Format("{stream_url}"),
            id="stream_url_btn",
            when="has_stream",
        ),
        Row(
            SwitchTo(
                Const("❓ Задать вопрос"),
                id="ask_question_btn",
                state=LectorySG.ASK_QUESTION,
            ),
            SwitchTo(
                Const("📋 Мои вопросы"),
                id="my_questions_btn",
                state=LectorySG.MY_QUESTIONS,
            ),
        ),
        Back(Const("◀️ Назад")),
        getter=get_event_detail,
        state=LectorySG.EVENT_DETAIL,
    ),

    # -----------------------------------------------------------------------
    # ASK_QUESTION — text input for submitting a question
    # -----------------------------------------------------------------------
    Window(
        Const(_ASK_QUESTION_TEXT),
        TextInput(
            id="question_input",
            type_factory=question_validator,
            on_success=on_question_submitted,
            on_error=on_question_error,
        ),
        SwitchTo(Const("❌ Отмена"), id="cancel_question", state=LectorySG.EVENT_DETAIL),
        state=LectorySG.ASK_QUESTION,
    ),

    # -----------------------------------------------------------------------
    # MY_QUESTIONS — list of user's questions + answers for this event
    # -----------------------------------------------------------------------
    Window(
        Format(
            "📋 <b>Мои вопросы</b>\n"
            "<i>{event_name}</i>\n\n"
            "{questions_text}"
        ),
        SwitchTo(Const("◀️ Назад"), id="back_from_my_questions", state=LectorySG.EVENT_DETAIL),
        getter=get_my_questions,
        state=LectorySG.MY_QUESTIONS,
    ),
)
