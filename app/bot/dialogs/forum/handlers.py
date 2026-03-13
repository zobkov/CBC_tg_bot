"""Handlers for the forum dialog."""
from __future__ import annotations

import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select

from app.infrastructure.database.database.db import DB
from app.services.tracks_config import get_track_by_key

logger = logging.getLogger(__name__)


async def on_track_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    **_kwargs: Any,
) -> None:
    """Persist the newly selected track to the database."""
    # item_id is the short key — resolve it to the full track name for DB storage
    track_info = get_track_by_key(item_id)
    if not track_info:
        logger.error("on_track_selected: unknown track key '%s'", item_id)
        return
    track_name = track_info["name"]

    db: DB | None = dialog_manager.middleware_data.get("db")
    if db:
        try:
            await db.forum_registrations.update_track(
                user_id=callback.from_user.id,
                track=track_name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "on_track_selected: DB error for user %d: %s",
                callback.from_user.id,
                exc,
            )
    # Window rerenders automatically via getter after handler completes
