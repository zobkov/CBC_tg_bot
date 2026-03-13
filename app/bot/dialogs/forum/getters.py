"""Data getters for the forum dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB
from app.services.tracks_config import get_track_by_name, get_track_by_key, load_tracks, resolve_track_name

logger = logging.getLogger(__name__)

_NO_TRACK = "Не определён"
_NO_CURATOR = "Не назначен"


async def get_forum_main(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return user_track and track_curator for the MAIN window."""
    db: DB | None = dialog_manager.middleware_data.get("db")

    user_track = _NO_TRACK
    is_registered = False
    if db:
        try:
            reg = await db.forum_registrations.get_by_user_id(user_id=event_from_user.id)
            if reg:
                is_registered = True
                if reg.get("track"):
                    user_track = resolve_track_name(reg["track"])
        except Exception as exc:  # noqa: BLE001
            logger.error("get_forum_main: DB error for user %d: %s", event_from_user.id, exc)

    track_info = get_track_by_name(user_track)
    track_curator = track_info["curator"] if track_info else _NO_CURATOR

    return {
        "user_track": user_track,
        "track_curator": track_curator,
        "is_not_registered": not is_registered,
    }


async def get_tracks_info(
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return a formatted numbered list of all active tracks."""
    tracks = load_tracks()
    lines: list[str] = []
    number = 1
    for track in tracks:
        if not track.get("active", True):
            continue
        name = track.get("name", "")
        description = track.get("description", "")
        lines.append(f"{number}. <b>{name}</b>\n{description}")
        number += 1

    return {"tracks_info": "\n\n".join(lines)}


async def get_change_track(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Return user_track and tracks list for the change_track window."""
    db: DB | None = dialog_manager.middleware_data.get("db")

    user_track = _NO_TRACK
    if db:
        try:
            reg = await db.forum_registrations.get_by_user_id(user_id=event_from_user.id)
            if reg and reg.get("track"):
                user_track = resolve_track_name(reg["track"])
        except Exception as exc:  # noqa: BLE001
            logger.error("get_change_track: DB error for user %d: %s", event_from_user.id, exc)

    tracks = load_tracks()
    items: list[tuple[str, str]] = []
    available_lines: list[str] = []
    number = 1
    for track in tracks:
        if not track.get("active", True):
            continue
        name = track.get("name", "")
        key = track.get("key", "")
        is_current = name == user_track
        prefix = "✅ " if is_current else ""
        label = f"{prefix}{number} – {name}"
        items.append((label, key))
        available_lines.append(f"{number}. {name}")
        number += 1

    return {
        "user_track": user_track,
        "tracks": items,
        "available_tracks": "\n".join(available_lines),
    }
