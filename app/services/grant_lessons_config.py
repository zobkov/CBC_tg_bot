"""Module-level cache for grant lesson configuration loaded from JSON."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/grant_lessons.json")
_LESSONS_CACHE: list[dict[str, Any]] | None = None


def load_grant_lessons(force: bool = False) -> list[dict[str, Any]]:
    """Return the list of grant lessons, loading from disk if necessary.

    Args:
        force: When *True* the cache is discarded and the file is re-read.

    Returns:
        List of lesson dicts, each with keys ``tag``, ``name``,
        ``description``, and ``url``.
    """
    global _LESSONS_CACHE  # noqa: PLW0603
    if _LESSONS_CACHE is None or force:
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as fh:
                _LESSONS_CACHE = json.load(fh)
            logger.info(
                "Grant lessons config loaded: %d lessons", len(_LESSONS_CACHE)
            )
        except FileNotFoundError:
            logger.error("grant_lessons.json not found at %s", _CONFIG_PATH)
            _LESSONS_CACHE = []
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse grant_lessons.json: %s", exc)
            _LESSONS_CACHE = []
    return _LESSONS_CACHE


def get_lesson_by_tag(tag: str) -> dict[str, Any] | None:
    """Return a single lesson dict by its tag, or *None* if not found."""
    for lesson in load_grant_lessons():
        if lesson.get("tag") == tag:
            return lesson
    return None
