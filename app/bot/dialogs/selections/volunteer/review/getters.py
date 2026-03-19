"""Getters for the volunteer review dialog."""

import logging
import math
from typing import Any

from aiogram_dialog import DialogManager

logger = logging.getLogger(__name__)

_PAGE_SIZE = 10

_YES_NO = {"yes": "Да", "no": "Нет"}
_Q1_MAP = {
    "1ый": "1ый",
    "2ой": "2ой",
    "3ий": "3ий",
    "4ый": "4ый",
    "5ый": "5ый",
}


def _yn(value: str | None) -> str:
    if value is None:
        return "—"
    return _YES_NO.get(value, value)


def _v(value: str | None) -> str:
    return value or "—"


async def get_page_select_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Build the list of page buttons."""
    from app.infrastructure.database.database.db import DB

    db: DB | None = dialog_manager.middleware_data.get("db")
    total = 0
    if db:
        try:
            total = await db.volunteer_selection_part2.count_all()
        except Exception as exc:
            logger.error("[VOL_REVIEW] count_all failed: %s", exc)

    total_pages = max(1, math.ceil(total / _PAGE_SIZE))
    pages = [(str(i), f"Стр {i + 1}") for i in range(total_pages)]

    return {
        "pages": pages,
        "total": total,
        "total_pages": total_pages,
    }


async def get_page_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Load one page of applications."""
    from app.infrastructure.database.database.db import DB

    db: DB | None = dialog_manager.middleware_data.get("db")
    current_page: int = dialog_manager.dialog_data.get("current_page", 0)

    apps: list[tuple[str, str]] = []
    total = 0

    if db:
        try:
            total = await db.volunteer_selection_part2.count_all()
            entities = await db.volunteer_selection_part2.list_page(
                page=current_page, limit=_PAGE_SIZE
            )
            for entity in entities:
                user_info = None
                try:
                    user_info = await db.users_info.get_user_info(user_id=entity.user_id)
                except Exception:
                    pass
                display = (
                    user_info.full_name
                    if user_info and user_info.full_name
                    else f"user_{entity.user_id}"
                )
                if entity.reviewed:
                    display = f"👀 {display}"
                apps.append((str(entity.user_id), display))
        except Exception as exc:
            logger.error("[VOL_REVIEW] get_page_data failed: %s", exc)

    total_pages = max(1, math.ceil(total / _PAGE_SIZE))
    has_prev = current_page > 0
    has_next = current_page < total_pages - 1

    return {
        "apps": apps,
        "has_prev": has_prev,
        "has_next": has_next,
        "page_label": f"Стр {current_page + 1}/{total_pages}",
        "current_page": current_page,
    }


async def get_app_detail_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Load the selected application and build a formatted text."""
    from app.infrastructure.database.database.db import DB

    db: DB | None = dialog_manager.middleware_data.get("db")
    selected_user_id: int | None = dialog_manager.dialog_data.get("selected_user_id")

    detail_text = "⚠️ Заявка не найдена."
    has_videos = False
    is_reviewed = False

    if db and selected_user_id is not None:
        try:
            app = await db.volunteer_selection_part2.get(user_id=selected_user_id)
            user_info = None
            try:
                user_info = await db.users_info.get_user_info(user_id=selected_user_id)
            except Exception:
                pass

            if app:
                has_videos = bool(app.vq1_file_id and app.vq2_file_id and app.vq3_file_id)
                is_reviewed = app.reviewed
                name = (user_info.full_name if user_info and user_info.full_name else f"user_{selected_user_id}")
                email = _v(user_info.email if user_info else None)
                education = _v(user_info.education if user_info else None)
                phone = _v(user_info.phone if user_info else None)

                tour_block = ""
                if app.q7_want_tour == "yes":
                    tour_block = (
                        f"\n<b>Опыт экскурсий:</b> {_yn(app.q7_has_tour_experience)}"
                        f"\n<b>Маршрут:</b> {_v(app.q7_tour_route)}"
                    )

                detail_text = (
                    f"👤 <b>{name}</b>\n"
                    f"📧 {email} | 🎓 {education} | 📱 {phone}\n\n"
                    f"<b>Q1 – Порядковый номер КБК:</b> {_v(app.q1_kbc_ordinal)}\n"
                    f"<b>Q2 – Дата КБК:</b> {_v(app.q2_kbc_date)}\n"
                    f"<b>Q3 – Тематика КБК:</b> {_v(app.q3_kbc_theme)}\n\n"
                    f"<b>Q4 – Команда:</b>\n{_v(app.q4_team_experience)}\n\n"
                    f"<b>Q5 – Бейджик:</b>\n{_v(app.q5_badge_case)}\n\n"
                    f"<b>Q6 – Иностранный гость:</b>\n{_v(app.q6_foreign_guest_case)}\n\n"
                    f"<b>Q7 – Хочет экскурсии:</b> {_yn(app.q7_want_tour)}"
                    f"{tour_block}"
                )
        except Exception as exc:
            logger.error("[VOL_REVIEW] get_app_detail_data failed: %s", exc)
            detail_text = f"❌ Ошибка загрузки: {exc}"

    return {
        "detail_text": detail_text,
        "has_videos": has_videos,
        "is_reviewed": is_reviewed,
        "not_is_reviewed": not is_reviewed,
    }


async def get_video_data(
    dialog_manager: DialogManager,
    **_kwargs: Any,
) -> dict[str, Any]:
    from app.infrastructure.database.database.db import DB

    db: DB | None = dialog_manager.middleware_data.get("db")
    selected_user_id: int | None = dialog_manager.dialog_data.get("selected_user_id")

    full_name = None
    if db and selected_user_id is not None:
        try:
            user_info = await db.users_info.get_user_info(user_id=selected_user_id)
            if user_info:
                full_name = user_info.full_name
        except Exception:
            pass

    name_line = full_name or f"user_{selected_user_id}"
    return {
        "video_header": (
            f"🎥 <b>Видео-интервью</b>\n"
            f"👤 {name_line}\n\n"
            "Кружки отправлены ниже"
        ),
    }
