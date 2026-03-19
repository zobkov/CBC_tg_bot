"""
Сервис для синхронизации заявок волонтёрского отбора (этап 2) с Google Sheets.
"""
import logging
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.volunteer_selection_part2 import VolSelPart2Model
from app.infrastructure.database.models.user_info import UsersInfoModel
from config.config import load_config

logger = logging.getLogger(__name__)

_YES_NO = {"yes": "Да", "no": "Нет"}


class VolunteerPart2GoogleSheetsSync:
    """Сервис для синхронизации заявок волонтёрского отбора (этап 2) с Google Sheets."""

    SPREADSHEET_ID = "1jxr_eYgEVEvXRq175fFNdQIrLG_z9XQ_nSjTFZZSBss"
    SHEET_NAME = "applications_part2"

    def __init__(self, db: DB):
        self.db = db
        self.config = load_config()
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self._setup_service()

    def _setup_service(self) -> None:
        """Настройка Google Sheets API."""
        try:
            credentials = Credentials.from_service_account_file(
                self.config.google.credentials_path, scopes=self.scopes
            )
            self.gc = gspread.authorize(credentials)
            logger.info("✅ Google Sheets API для заявок волонтёров (ч.2) настроен")
        except FileNotFoundError:
            logger.warning(
                "⚠️ Google credentials файл не найден. "
                "Синхронизация заявок (ч.2) с Google Sheets недоступна."
            )
            self.gc = None
        except Exception as exc:
            logger.error("❌ Ошибка настройки Google Sheets API (volunteer_part2): %s", exc)
            self.gc = None

    def _get_headers(self) -> list[str]:
        return [
            "ID",
            "User ID",
            "ФИО",
            "Email",
            "Образование",
            "Телефон",
            # Written questions
            "Q1 – Порядок КБК",
            "Q2 – Дата КБК",
            "Q3 – Тематика КБК",
            "Q4 – Команда",
            "Q5 – Бейджик",
            "Q6 – Иностр. гость",
            "Q7 – Хочет экскурсии",
            "Q7 – Опыт экскурсий",
            "Q7 – Маршрут",
            # Video interview
            "Видео 1",
            "Видео 2",
            "Видео 3",
            # Review flag
            "Просмотрено",
            # Meta
            "Дата заявки",
        ]

    @staticmethod
    def _yn(value: str | None) -> str:
        if value is None:
            return "—"
        return _YES_NO.get(value, value)

    @staticmethod
    def _v(value: str | None) -> str:
        return value or "—"

    def _format_row(
        self,
        app: VolSelPart2Model,
        user_info: UsersInfoModel | None,
    ) -> list[Any]:
        submitted_str = (
            app.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if app.submitted_at else ""
        )
        return [
            app.id or "",
            app.user_id,
            user_info.full_name if user_info else "",
            user_info.email if user_info else "",
            user_info.education if user_info else "",
            user_info.phone if user_info and hasattr(user_info, "phone") else "",
            # Written questions
            self._v(app.q1_kbc_ordinal),
            self._v(app.q2_kbc_date),
            self._v(app.q3_kbc_theme),
            self._v(app.q4_team_experience),
            self._v(app.q5_badge_case),
            self._v(app.q6_foreign_guest_case),
            self._yn(app.q7_want_tour),
            self._yn(app.q7_has_tour_experience),
            self._v(app.q7_tour_route),
            # Video interview (presence indicator)
            "✅" if app.vq1_file_id else "—",
            "✅" if app.vq2_file_id else "—",
            "✅" if app.vq3_file_id else "—",
            # Review flag
            "Да" if app.reviewed else "Нет",
            # Meta
            submitted_str,
        ]

    async def sync_all_applications(self) -> int:
        """
        Синхронизирует все заявки (этап 2) из БД в Google Sheets.

        Returns:
            int: Количество синхронизированных записей.
        """
        if self.gc is None:
            logger.warning(
                "[VOL_PART2_SYNC] Google Sheets client недоступен. Пропускаем синхронизацию."
            )
            return 0

        try:
            logger.info("[VOL_PART2_SYNC] Получаю заявки из БД...")
            applications = await self.db.volunteer_selection_part2.list_all()

            if not applications:
                logger.info("[VOL_PART2_SYNC] Нет заявок для синхронизации")
                return 0

            logger.info("[VOL_PART2_SYNC] Форматирую %d заявок...", len(applications))
            rows: list[list[Any]] = []
            for app in applications:
                user_info = await self.db.users_info.get_user_info(user_id=app.user_id)
                rows.append(self._format_row(app, user_info))

            logger.info("[VOL_PART2_SYNC] Открываю Google таблицу...")
            spreadsheet = self.gc.open_by_key(self.SPREADSHEET_ID)

            try:
                worksheet = spreadsheet.worksheet(self.SHEET_NAME)
                logger.info("[VOL_PART2_SYNC] Лист '%s' найден", self.SHEET_NAME)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(
                    "[VOL_PART2_SYNC] Лист '%s' не найден, создаю...", self.SHEET_NAME
                )
                worksheet = spreadsheet.add_worksheet(
                    title=self.SHEET_NAME, rows=1000, cols=25
                )

            logger.info("[VOL_PART2_SYNC] Очищаю существующие данные...")
            worksheet.clear()

            headers = self._get_headers()
            worksheet.append_row(headers, value_input_option="RAW")
            worksheet.append_rows(rows, value_input_option="RAW")

            logger.info(
                "[VOL_PART2_SYNC] Синхронизировано %d заявок в лист '%s'",
                len(rows),
                self.SHEET_NAME,
            )
            return len(rows)

        except Exception as exc:
            logger.error("[VOL_PART2_SYNC] Ошибка синхронизации: %s", exc, exc_info=True)
            raise
