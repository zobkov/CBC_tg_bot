"""Participant certificate service.

Loads the forum_registrations_with_gender.csv at import time and exposes
helpers to check eligibility and generate personalised PDF certificates.
"""

from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from app.utils.certificate_gen.generator import CertificateGenerator

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

class _ParticipantInfo(TypedDict):
    full_name: str
    gender: str   # "M" or "F"
    track: str    # English track slug


_CSV_PATH = Path("forum_registrations_with_gender.csv")

try:
    with _CSV_PATH.open(newline="", encoding="utf-8") as _f:
        _reader = csv.DictReader(_f)
        _CERT_PARTICIPANTS: dict[int, _ParticipantInfo] = {
            int(row["user_id"]): {
                "full_name": row["full_name"].strip(),
                "gender": row["gender"].strip().upper(),
                "track": row["track"].strip(),
            }
            for row in _reader
            if row.get("user_id", "").strip().isdigit()
        }
    LOGGER.info(
        "Loaded %d participant cert entries from %s",
        len(_CERT_PARTICIPANTS),
        _CSV_PATH,
    )
except FileNotFoundError:
    _CERT_PARTICIPANTS = {}
    LOGGER.warning(
        "%s not found — participant cert button hidden for all non-admins",
        _CSV_PATH,
    )

# ---------------------------------------------------------------------------
# Track name mapping (CSV slugs → Russian)
# ---------------------------------------------------------------------------

_TRACK_NAMES_RU: dict[str, str] = {
    "politics": "Политика, право и дипломатия ",
    "logistics": "Логистика и ВЭД",
    "marketing": "Маркетинг и медиа",
    "finance": "Финансы и инвестиции",
    "consulting": "Консалтинг и риск-менеджмент",
    "chinese": "Международные студенты",
    "language": "Язык, культура и перевод",
    "rosmolodezh_grants": "Росмолодёжь.Гранты",
}

# ---------------------------------------------------------------------------
# Generator factories (singletons per gender)
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "utils" / "certificate_gen"
_OUTPUT_DIR = Path("temp/participant_cert")


@lru_cache(maxsize=1)
def _get_gen_m() -> CertificateGenerator:
    return CertificateGenerator(
        output_dir=_OUTPUT_DIR,
        template_path=_TEMPLATE_DIR / "certificate_participant_m.html",
        page_style=None,  # @page dimensions are defined inside the template
    )


@lru_cache(maxsize=1)
def _get_gen_f() -> CertificateGenerator:
    return CertificateGenerator(
        output_dir=_OUTPUT_DIR,
        template_path=_TEMPLATE_DIR / "certificate_participant_f.html",
        page_style=None,  # @page dimensions are defined inside the template
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_cert_eligible(user_id: int) -> bool:
    """Return True if the user is in the participants CSV."""
    return user_id in _CERT_PARTICIPANTS


def get_participant_info(user_id: int) -> _ParticipantInfo | None:
    """Return participant data or None if the user is not in the CSV."""
    return _CERT_PARTICIPANTS.get(user_id)


def _build_cert_filename(full_name: str) -> str:
    """Build deterministic Russian filename.

    "Николаева Алиса Александровна" → "НиколаеваА_КБК_Сертификат_участника.pdf"
    """
    parts = full_name.strip().split()
    last_name = parts[0] if parts else "Участник"
    first_initial = parts[1][0] if len(parts) > 1 else ""
    # Keep only word characters (Cyrillic + latin + digits) to stay filesystem-safe
    safe_last = re.sub(r"[^\w]", "", last_name, flags=re.UNICODE)
    safe_initial = re.sub(r"[^\w]", "", first_initial, flags=re.UNICODE)
    return f"{safe_last}{safe_initial}_КБК_Сертификат_участника.pdf"


def _name_patronymic(full_name: str) -> str:
    """Extract «Имя Отчество» from a full name «Фамилия Имя Отчество».

    Falls back gracefully if parts are missing.
    """
    parts = full_name.strip().split()
    if len(parts) >= 3:
        return f"{parts[1]} {parts[2]}"
    if len(parts) == 2:
        return parts[1]
    return full_name


def generate_cert_for_db_user(
    user_id: int,
    full_name: str,
    gender: str,
    track: str,
) -> Path:
    """Generate (or return cached) a cert for a user found in DB but not in CSV.

    Args:
        user_id: Telegram user ID (used only for debug logging).
        full_name: Full name string as stored in bot_forum_registrations.name.
        gender: ``"M"`` or ``"F"``.
        track: Track slug as stored in DB (mapped to Russian via ``_TRACK_NAMES_RU``).

    Returns the ``Path`` to the generated PDF.
    Raises ``CertificateGenerationError`` on render failures.
    """
    track_ru = _TRACK_NAMES_RU.get(track, track) if track else "Форум КБК'26"
    filename = _build_cert_filename(full_name)
    cert_path = _OUTPUT_DIR / filename

    if cert_path.exists():
        LOGGER.debug("Returning cached cert for user %d: %s", user_id, cert_path)
        return cert_path

    gen = _get_gen_m() if gender.upper() == "M" else _get_gen_f()
    io_name = _name_patronymic(full_name)

    return gen.generate(
        full_name,
        output_filename=filename,
        substitutions={
            "ИО_PLACEHOLDER": io_name,
            "ТРЕК_PLACEHOLDER": track_ru,
        },
    )


def generate_cert(user_id: int) -> Path:
    """Generate (or return cached) a participation certificate for *user_id*.

    Returns the ``Path`` to the generated PDF.
    Raises ``KeyError`` if the user is not in the participants list.
    Raises ``CertificateGenerationError`` on render failures.
    """
    info = _CERT_PARTICIPANTS[user_id]
    full_name = info["full_name"]
    gender = info["gender"]
    track_ru = _TRACK_NAMES_RU.get(info["track"], info["track"])

    filename = _build_cert_filename(full_name)
    cert_path = _OUTPUT_DIR / filename

    # Return cached file without re-rendering
    if cert_path.exists():
        LOGGER.debug("Returning cached cert for user %d: %s", user_id, cert_path)
        return cert_path

    gen = _get_gen_m() if gender == "M" else _get_gen_f()
    io_name = _name_patronymic(full_name)

    return gen.generate(
        full_name,
        output_filename=filename,
        substitutions={
            "ИО_PLACEHOLDER": io_name,
            "ТРЕК_PLACEHOLDER": track_ru,
        },
    )
