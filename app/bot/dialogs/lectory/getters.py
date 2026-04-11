"""Data getters for the lectory dialog."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB
from app.services.tracks_config import get_track_by_name, resolve_track_name

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/lectory.json")
_LECTORY_DATA: dict[str, Any] = {}

try:
    with open(_CONFIG_PATH, encoding="utf-8") as _fh:
        _LECTORY_DATA = json.load(_fh)
    logger.info("Lectory config loaded")
except (FileNotFoundError, json.JSONDecodeError) as _exc:
    logger.error("Failed to load lectory.json: %s", _exc)

_COMMON_EVENTS: list[dict[str, Any]] = _LECTORY_DATA.get("common", [])
_TRACK_DATA: dict[str, Any] = _LECTORY_DATA.get("tracks", {})

_COMMON_OVERVIEW = (
    "10:30 Открытие  |  11:30 Панель 1\n"
    "16:30 Панель 2  |  20:00 Закрытие"
)

_MAX_LABEL_NAME = 45


def _truncate(text: str, max_len: int = _MAX_LABEL_NAME) -> str:
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"


async def _resolve_track_key(dialog_manager: DialogManager, user_id: int) -> str:
    """Return the short track key for the user, or empty string."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    if not db:
        return ""
    try:
        reg = await db.forum_registrations.get_by_user_id(user_id=user_id)
        if reg and reg.get("track"):
            track_name = resolve_track_name(reg["track"])
            track_info = get_track_by_name(track_name)
            if track_info:
                return track_info.get("key", "")
    except Exception as exc:
        logger.error("_resolve_track_key: DB error for user %d: %s", user_id, exc)
    return ""


async def get_schedule(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return schedule data for the SCHEDULE window."""
    db: DB | None = dialog_manager.middleware_data.get("db")

    track_name = ""
    track_key = ""
    if db:
        try:
            reg = await db.forum_registrations.get_by_user_id(user_id=event_from_user.id)
            if reg and reg.get("track"):
                track_name = resolve_track_name(reg["track"])
                track_info = get_track_by_name(track_name)
                if track_info:
                    track_key = track_info.get("key", "")
        except Exception as exc:
            logger.error("get_schedule: DB error for user %d: %s", event_from_user.id, exc)

    has_track = bool(track_name)
    track_events: list[dict[str, Any]] = []
    if track_key:
        track_events = _TRACK_DATA.get(track_key, {}).get("events", [])

    has_events = bool(track_events)
    has_track_no_events = has_track and not has_events

    short_track = track_name.split("(")[0].strip() if track_name else ""

    schedule_text = (
        f"📅 <b>Расписание — {short_track}</b>\n\n"
        f"{_COMMON_OVERVIEW}\n\n"
        "Мероприятия трека:"
    ) if has_track else ""

    events: list[tuple[str, str]] = []
    for ev in track_events:
        name = ev.get("name", "")
        time = ev.get("time", "")
        label = f"{time} | {_truncate(name)}"
        events.append((label, ev["key"]))

    return {
        "track_name": short_track,
        "has_track": has_track,
        "has_events": has_events,
        "has_track_no_events": has_track_no_events,
        "schedule_text": schedule_text,
        "events": events,
    }


def _find_event(event_key: str, track_key: str) -> dict[str, Any] | None:
    """Search common events then track events for the given key."""
    for ev in _COMMON_EVENTS:
        if ev.get("key") == event_key:
            return ev
    for ev in _TRACK_DATA.get(track_key, {}).get("events", []):
        if ev.get("key") == event_key:
            return ev
    return None


async def get_event_detail(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return event detail data for the EVENT_DETAIL window."""
    event_key: str = dialog_manager.dialog_data.get("selected_event", "")
    track_key = await _resolve_track_key(dialog_manager, event_from_user.id)

    ev = _find_event(event_key, track_key) or {}
    event_name = ev.get("name", "")

    # Store event name in dialog_data so ASK_QUESTION handler can read it
    dialog_manager.dialog_data["selected_event_name"] = event_name

    stream_url = ev.get("stream_url", "")
    description = ev.get("description", "")
    event_format = ev.get("format", "")
    question_submitted = dialog_manager.dialog_data.get("question_submitted", False)

    return {
        "event_name": event_name,
        "event_time": ev.get("time", ""),
        "event_auditorium": ev.get("auditorium", ""),
        "event_format": event_format,
        "event_description": description,
        "has_stream": bool(stream_url),
        "stream_url": stream_url,
        "has_format": bool(event_format),
        "has_description": bool(description),
        "question_submitted": question_submitted,
    }


async def get_my_questions(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return the user's Q&A list for the current event."""
    event_key: str = dialog_manager.dialog_data.get("selected_event", "")
    event_name: str = dialog_manager.dialog_data.get("selected_event_name", "")

    db: DB | None = dialog_manager.middleware_data.get("db")
    questions: list[dict[str, Any]] = []
    if db:
        try:
            questions = await db.lectory_questions.get_user_questions_for_event(
                user_id=event_from_user.id,
                event_key=event_key,
            )
        except Exception as exc:
            logger.error("get_my_questions: DB error for user %d: %s", event_from_user.id, exc)

    if questions:
        lines: list[str] = []
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q['question_text']}")
            if q.get("answer_text"):
                lines.append(f"   💬 <i>{q['answer_text']}</i>")
            else:
                lines.append("   ⏳ <i>Ответ пока не получен</i>")
        questions_text = "\n\n".join(lines)
    else:
        questions_text = "Ты ещё не задавал вопросов к этому мероприятию."

    short_name = _truncate(event_name, 50)

    return {
        "event_name": short_name,
        "questions_text": questions_text,
        "has_questions": bool(questions),
    }
