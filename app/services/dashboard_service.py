"""Build the registration dashboard report text."""

from __future__ import annotations

# Ordered list of (track_key, display_name) matching the spec and tracks_config.json order.
_TRACKS: list[tuple[str, str]] = [
    ("finance", "Финансы и инвестиции (Finance & Banking)"),
    ("logistics", "Логистика и ВЭД (Supply Chain & Trade)"),
    ("consulting", "Консалтинг и риск-менеджмент (Strategy & Consulting)"),
    ("policy", "Политика, право и дипломатия (Rules of the Game)"),
    ("marketing", "Маркетинг и медиа (Digital & Brand)"),
    ("humanities", "Язык, культура и перевод (Humanities & Arts)"),
    ("chinese", "Китайский трек (Chinese Track)"),
    ("project_management", "Росмолодёжь.Гранты"),
]


def build_report_text(stats: dict) -> str:
    """Format dashboard stats dict into an HTML Telegram message.

    Args:
        stats: dict returned by ``_ForumRegistrationsDB.get_dashboard_stats()``.

    Returns:
        HTML-formatted report string ready to send via ``parse_mode="HTML"``.
    """
    site_total: int = stats.get("site_total", 0)
    bot_total: int = stats.get("bot_total", 0)
    site_by_track: dict[str, int] = stats.get("site_by_track", {})
    bot_by_track: dict[str, int] = stats.get("bot_by_track", {})
    site_by_status: dict[str, int] = stats.get("site_by_status", {})
    bot_by_status: dict[str, int] = stats.get("bot_by_status", {})

    if site_total > 0:
        conversion = round(bot_total / site_total * 100, 1)
    else:
        conversion = 0.0

    lines: list[str] = [
        "<b>Отчет по регистрациям</b>",
        "",
        f"Кол-во регистраций на сайте: <b>{site_total}</b>",
        f"Кол-во регистраций в боте: <b>{bot_total}</b>",
        f"Конверсия: <b>{conversion}%</b>",
        "",
        "<b>Регистрации по трекам:</b>",
    ]

    for idx, (key, display_name) in enumerate(_TRACKS, start=1):
        bot_n = bot_by_track.get(key, 0)
        site_n = site_by_track.get(key, 0)
        lines.append(f"{idx}. {display_name} — {bot_n} / {site_n}")

    # Status breakdown
    all_status_keys = sorted(
        set(site_by_status) | set(bot_by_status),
        key=lambda s: s.lower(),
    )
    if all_status_keys:
        lines.append("")
        lines.append("<b>Регистрации по статусам:</b>")
        for status in all_status_keys:
            label = status if status else "(не указан)"
            bot_n = bot_by_status.get(status, 0)
            site_n = site_by_status.get(status, 0)
            lines.append(f"• {label} — {bot_n} / {site_n}")

    return "\n".join(lines)
