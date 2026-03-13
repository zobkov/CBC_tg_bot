"""Module-level cache for forum track configuration loaded from JSON."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/tracks_config.json")
_TRACKS_CACHE: list[dict[str, Any]] | None = None


def load_tracks(force: bool = False) -> list[dict[str, Any]]:
    """Return the list of tracks, loading from disk if necessary.

    Args:
        force: When *True* the cache is discarded and the file is re-read.

    Returns:
        List of track dicts, each with keys ``key``, ``name``,
        ``description``, ``curator``, and ``active``.
    """
    global _TRACKS_CACHE  # noqa: PLW0603
    if _TRACKS_CACHE is None or force:
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as fh:
                _TRACKS_CACHE = json.load(fh)
            logger.info("Tracks config loaded: %d tracks", len(_TRACKS_CACHE))
        except FileNotFoundError:
            logger.error("tracks_config.json not found at %s", _CONFIG_PATH)
            _TRACKS_CACHE = []
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse tracks_config.json: %s", exc)
            _TRACKS_CACHE = []
    return _TRACKS_CACHE


def get_track_by_name(name: str) -> dict[str, Any] | None:
    """Return a single track dict by its full name, or *None* if not found."""
    for track in load_tracks():
        if track.get("name") == name:
            return track
    return None
