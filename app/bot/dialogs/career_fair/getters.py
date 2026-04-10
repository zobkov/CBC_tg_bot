"""Data getters для диалога Ярмарки карьеры."""
import json
import logging
from pathlib import Path
from typing import Any

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from app.utils.optimized_dialog_widgets import get_file_id_for_path

logger = logging.getLogger(__name__)

_CAREER_INFO_PATH = Path("config/career_info.json")

try:
    with _CAREER_INFO_PATH.open(encoding="utf-8") as _f:
        _CAREER_DATA: list[dict] = json.load(_f)
    logger.info("Loaded career_info.json: %d tracks", len(_CAREER_DATA))
except (FileNotFoundError, json.JSONDecodeError) as _e:
    _CAREER_DATA = []
    logger.error("Failed to load career_info.json: %s", _e)

# Build lookup indices for fast access
_TRACKS_BY_KEY: dict[str, dict] = {track["key"]: track for track in _CAREER_DATA}
_COMPANIES_BY_KEY: dict[str, dict] = {
    company["key"]: company
    for track in _CAREER_DATA
    for company in track.get("companies", [])
}


async def get_tracks(**_kwargs: Any) -> dict[str, Any]:
    """Return list of (track_name, track_key) tuples for the Select widget."""
    tracks = [(track["name"], track["key"]) for track in _CAREER_DATA]
    return {"tracks": tracks}


async def get_companies(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Return companies for the selected track."""
    selected_track_key = dialog_manager.dialog_data.get("selected_track", "")
    track = _TRACKS_BY_KEY.get(selected_track_key)

    if not track:
        return {"companies": [], "track_name": ""}

    companies = [(company["name"], company["key"]) for company in track.get("companies", [])]
    return {
        "companies": companies,
        "track_name": track["name"],
    }


def _resolve_media(image_path: str):
    """Return (MediaAttachment | None, has_image: bool) for the given relative image path."""
    if not image_path:
        return None, False
    file_id = get_file_id_for_path(image_path)
    if file_id:
        return MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id)), True
    full_path = Path("app/bot/assets/images") / image_path
    if full_path.exists():
        return MediaAttachment(type=ContentType.PHOTO, path=str(full_path)), True
    return None, False


async def get_company_detail(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Return company image, name and description (no vacancies — caption limit is 1024 chars)."""
    selected_company_key = dialog_manager.dialog_data.get("selected_company", "")
    company = _COMPANIES_BY_KEY.get(selected_company_key)

    if not company:
        return {
            "company_header": "Информация о компании недоступна.",
            "media": None,
            "has_image": False,
            "has_vacancies": False,
        }

    name = company.get("name", "")
    description = company.get("description", "")
    vacancies = company.get("vacancies", [])

    # Short text safe for a photo caption (≤1024 chars)
    header_parts = [f"<b>{name}</b>"]
    if description:
        header_parts.append(f"\n{description}")
    company_header = "\n".join(header_parts)

    media, has_image = _resolve_media(company.get("image", ""))

    return {
        "company_header": company_header,
        "media": media,
        "has_image": has_image,
        "has_vacancies": bool(vacancies),
    }


async def get_company_vacancies(dialog_manager: DialogManager, **_kwargs: Any) -> dict[str, Any]:
    """Return vacancy links as HTML text (text-only window, 4096 char limit)."""
    selected_company_key = dialog_manager.dialog_data.get("selected_company", "")
    company = _COMPANIES_BY_KEY.get(selected_company_key)

    if not company:
        return {"vacancies_text": "Вакансии недоступны."}

    name = company.get("name", "")
    vacancies = company.get("vacancies", [])

    parts = [f"<b>Вакансии — {name}</b>"]
    for vacancy in vacancies:
        title = vacancy.get("title", "")
        url = vacancy.get("url", "")
        if url:
            parts.append(f'\n• <a href="{url}">{title}</a>')
        else:
            parts.append(f"\n• {title}")

    return {"vacancies_text": "\n".join(parts)}
