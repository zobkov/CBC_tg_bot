"""Dialog definition for the Лекторий (lecture schedule) section."""
import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Group, Select, Url
from aiogram_dialog.widgets.text import Const, Format

from .getters import get_event_detail, get_schedule
from .handlers import on_event_selected
from .states import LectorySG

_NO_TRACK_TEXT = (
    "📅 <b>Лекторий</b>\n\n"
    "Выбери трек, чтобы увидеть расписание мероприятий."
)

_NO_EVENTS_TEXT = (
    "📅 <b>Лекторий</b>\n\n"
    "Расписание мероприятий трека уточняется."
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
    # EVENT_DETAIL — individual event info
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
        Url(
            Const("🔗 Трансляция"),
            Format("{stream_url}"),
            id="stream_url_btn",
            when="has_stream",
        ),
        Back(Const("◀️ Назад")),
        getter=get_event_detail,
        state=LectorySG.EVENT_DETAIL,
    ),
)
