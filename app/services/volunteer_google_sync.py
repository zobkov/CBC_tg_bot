"""
Сервис для синхронизации волонтёрских заявок с Google Sheets.
"""
import logging
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.volunteer_application import VolunteerApplicationModel
from app.infrastructure.database.models.user_info import UsersInfoModel
from config.config import load_config

logger = logging.getLogger(__name__)

_FUNCTION_LABELS = {
    "general": "Общий",
    "photo": "Фотографирование",
    "translate": "Перевод",
}
_DATES_LABELS = {
    "single": "Только 11 апреля",
    "double": "10 и 11 апреля",
}
_YES_NO = {"yes": "Да", "no": "Нет"}
_G1_LABELS = {
    "guest": "Да, участник",
    "volunteer": "Да, волонтер",
    "guest_and_volunteer": "Да, оба",
    "no": "Нет",
}


class VolunteerGoogleSheetsSync:
    """Сервис для синхронизации волонтёрских заявок с Google Sheets."""

    SPREADSHEET_ID = "1jxr_eYgEVEvXRq175fFNdQIrLG_z9XQ_nSjTFZZSBss"
    SHEET_NAME = "Applications"

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
            logger.info("✅ Google Sheets API для волонтёрских заявок настроен")
        except FileNotFoundError:
            logger.warning(
                "⚠️ Google credentials файл не найден. "
                "Синхронизация волонтёров с Google Sheets недоступна."
            )
            self.gc = None
        except Exception as exc:
            logger.error("❌ Ошибка настройки Google Sheets API (volunteer): %s", exc)
            self.gc = None

    def _get_headers(self) -> list[str]:
        return [
            "ID",
            "User ID",
            "ФИО",
            "Email",
            "Образование",
            "Телефон",
            "Даты",
            "Функционал",
            # General
            "КБК ранее (тип)",
            "КБК ранее (ответ)",
            "Почему КБК",
            "Личные качества",
            "Доп. инфо (Общий)",
            # Photo
            "Портфолио",
            "Своё оборудование",
            "Опыт съёмки",
            "Ключевые моменты",
            "Доп. инфо (Фото)",
            # Translate
            "Уровень китайского",
            "Сертификат",
            "Ссылка на сертификат",
            "Опыт общения на кит.",
            "Опыт работы с иностр.",
            "Ситуация с переводом",
            "Доп. инфо (Перевод)",
            # Common
            "Дата заявки",
        ]

    def _format_row(
        self,
        app: VolunteerApplicationModel,
        user_info: UsersInfoModel | None,
    ) -> list[Any]:
        submitted_str = (
            app.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if app.submitted_at else ""
        )
        # Handle comma-separated roles (multi-role submissions)
        function_str = ", ".join(
            _FUNCTION_LABELS.get(r.strip(), r.strip())
            for r in (app.function or "").split(",")
            if r.strip()
        )
        return [
            app.id or "",
            app.user_id,
            user_info.full_name if user_info else "",
            user_info.email if user_info else "",
            user_info.education if user_info else "",
            app.phone or "",
            _DATES_LABELS.get(app.volunteer_dates or "", app.volunteer_dates or ""),
            function_str,
            # General
            _G1_LABELS.get(app.general_1_type or "", app.general_1_type or ""),
            app.general_1_answer or "",
            app.general_2 or "",
            app.general_3 or "",
            app.general_additional_information or "",
            # Photo
            app.photo_portfolio or "",
            _YES_NO.get(app.photo_has_equipment or "", app.photo_has_equipment or ""),
            app.photo_experience or "",
            app.photo_key_moments or "",
            app.photo_additional_information or "",
            # Translate
            app.translate_level or "",
            _YES_NO.get(app.translate_has_cert or "", app.translate_has_cert or ""),
            app.translate_cert_link or "",
            app.translate_experience_detail or "",
            app.translate_worked_with_foreigners or "",
            app.translate_difficult_situation or "",
            app.translate_additional_information or "",
            # Common
            submitted_str,
        ]

    async def sync_all_applications(self) -> int:
        """
        Синхронизирует все волонтёрские заявки из БД в Google Sheets.

        Returns:
            int: Количество синхронизированных записей.
        """
        if self.gc is None:
            logger.warning(
                "[VOLUNTEER_SYNC] Google Sheets client недоступен. Пропускаем синхронизацию."
            )
            return 0

        try:
            logger.info("[VOLUNTEER_SYNC] Получаю заявки из БД...")
            applications = await self.db.volunteer_applications.list_all()

            if not applications:
                logger.info("[VOLUNTEER_SYNC] Нет заявок для синхронизации")
                return 0

            logger.info("[VOLUNTEER_SYNC] Форматирую %d заявок...", len(applications))
            rows: list[list[Any]] = []
            for app in applications:
                user_info = await self.db.users_info.get_user_info(user_id=app.user_id)
                rows.append(self._format_row(app, user_info))

            logger.info("[VOLUNTEER_SYNC] Открываю Google таблицу...")
            spreadsheet = self.gc.open_by_key(self.SPREADSHEET_ID)

            try:
                worksheet = spreadsheet.worksheet(self.SHEET_NAME)
                logger.info("[VOLUNTEER_SYNC] Лист '%s' найден", self.SHEET_NAME)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(
                    "[VOLUNTEER_SYNC] Лист '%s' не найден, создаю...", self.SHEET_NAME
                )
                worksheet = spreadsheet.add_worksheet(
                    title=self.SHEET_NAME, rows=1000, cols=30
                )

            logger.info("[VOLUNTEER_SYNC] Очищаю существующие данные...")
            worksheet.clear()

            headers = self._get_headers()
            worksheet.append_row(headers, value_input_option="RAW")
            worksheet.append_rows(rows, value_input_option="RAW")

            logger.info(
                "[VOLUNTEER_SYNC] Синхронизировано %d заявок в лист '%s'",
                len(rows),
                self.SHEET_NAME,
            )
            return len(rows)

        except Exception as exc:
            logger.error("[VOLUNTEER_SYNC] Ошибка синхронизации: %s", exc, exc_info=True)
            raise
