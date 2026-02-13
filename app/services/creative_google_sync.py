"""
Сервис для синхронизации креативных заявок с Google Sheets
"""
import logging
from typing import Any
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.creative_application import (
    CreativeApplicationModel,
)
from app.infrastructure.database.models.user_info import UsersInfoModel
from config.config import load_config

logger = logging.getLogger(__name__)


class CreativeGoogleSheetsSync:
    """Сервис для синхронизации креативных заявок с Google Sheets"""

    SHEET_NAME = "Креатив"

    def __init__(self, db: DB):
        """
        Инициализация сервиса синхронизации

        Args:
            db: Database instance
        """
        self.db = db
        self.config = load_config()

        # Spreadsheet ID из конфигурации
        self.spreadsheet_id = self.config.google.spreadsheet_id

        # Области доступа
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        self._setup_service()

    def _setup_service(self):
        """Настройка Google Sheets API"""
        try:
            credentials = Credentials.from_service_account_file(
                self.config.google.credentials_path, scopes=self.scopes
            )

            self.gc = gspread.authorize(credentials)
            logger.info("✅ Google Sheets API для креативных заявок настроен")

        except FileNotFoundError:
            logger.warning(
                "⚠️ Google credentials файл не найден. "
                "Синхронизация с Google Sheets будет недоступна."
            )
            self.gc = None
        except Exception as e:
            logger.error(f"❌ Ошибка настройки Google Sheets API: {e}")
            self.gc = None

    def _get_headers(self) -> list[str]:
        """Возвращает заголовки колонок для таблицы"""
        return [
            "ID",
            "User ID",
            "ФИО",
            "Контакт",
            "Email",
            "Университет",
            "Направление",
            "Опыт на сцене",
            "Мотивация (церемония)",
            "Может посещать РМ",
            "Частота РМ",
            "Длительность РМ",
            "Слоты времени",
            "Облако (церемония)",
            "Роли (ярмарка)",
            "Мотивация (ярмарка)",
            "Опыт (ярмарка)",
            "Облако (ярмарка)",
            "Дата подачи",
            "Обновлено",
        ]

    def _format_application_row(
        self, app: CreativeApplicationModel, user_info: UsersInfoModel | None
    ) -> list[Any]:
        """
        Форматирует одну заявку в строку для таблицы

        Args:
            app: Модель заявки
            user_info: Информация о пользователе

        Returns:
            list: Список значений для строки таблицы
        """
        # Форматирование булевых значений
        can_attend_md = ""
        if app.ceremony_can_attend_md is not None:
            can_attend_md = "Да" if app.ceremony_can_attend_md else "Нет"

        # Форматирование массивов
        timeslots_str = ""
        if app.ceremony_timeslots:
            timeslots_str = ", ".join(app.ceremony_timeslots)

        fair_roles_str = ""
        if app.fair_roles:
            fair_roles_str = ", ".join(app.fair_roles)

        # Форматирование дат
        submitted_at_str = ""
        if app.submitted_at:
            submitted_at_str = app.submitted_at.strftime("%Y-%m-%d %H:%M:%S")

        updated_str = ""
        if app.updated:
            updated_str = app.updated.strftime("%Y-%m-%d %H:%M:%S")

        return [
            app.id or "",
            app.user_id,
            user_info.full_name if user_info else "",
            app.contact or "",
            user_info.email if user_info else "",
            user_info.education if user_info else "",
            app.direction,
            app.ceremony_stage_experience or "",
            app.ceremony_motivation or "",
            can_attend_md,
            app.ceremony_rehearsal_frequency or "",
            app.ceremony_rehearsal_duration or "",
            timeslots_str,
            app.ceremony_cloud_link or "",
            fair_roles_str,
            app.fair_motivation or "",
            app.fair_experience or "",
            app.fair_cloud_link or "",
            submitted_at_str,
            updated_str,
        ]

    async def sync_all_applications(self) -> int:
        """
        Синхронизирует все креативные заявки из БД в Google Sheets

        Returns:
            int: Количество синхронизированных записей
        """
        if self.gc is None:
            logger.warning(
                "[CREATIVE_SYNC] Google Sheets client недоступен. Пропускаем синхронизацию."
            )
            return 0

        try:
            # 1. Получить все заявки из БД
            logger.info("[CREATIVE_SYNC] Получаю заявки из БД...")
            applications = await self.db.creative_applications.list_all()

            if not applications:
                logger.info("[CREATIVE_SYNC] Нет заявок для синхронизации")
                return 0

            # 2. Для каждой заявки получить user_info
            logger.info(
                "[CREATIVE_SYNC] Форматирую %d заявок...", len(applications)
            )
            rows = []
            for app in applications:
                user_info = await self.db.users_info.get_user_info(
                    user_id=app.user_id
                )
                row = self._format_application_row(app, user_info)
                rows.append(row)

            # 3. Открыть таблицу
            logger.info("[CREATIVE_SYNC] Открываю Google таблицу...")
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)

            # 4. Получить или создать лист
            try:
                worksheet = spreadsheet.worksheet(self.SHEET_NAME)
                logger.info("[CREATIVE_SYNC] Лист '%s' найден", self.SHEET_NAME)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(
                    "[CREATIVE_SYNC] Лист '%s' не найден, создаю...",
                    self.SHEET_NAME,
                )
                worksheet = spreadsheet.add_worksheet(
                    title=self.SHEET_NAME, rows=1000, cols=20
                )

            # 5. Очистить и записать данные
            logger.info("[CREATIVE_SYNC] Очищаю существующие данные...")
            worksheet.clear()

            logger.info("[CREATIVE_SYNC] Записываю заголовки...")
            worksheet.append_row(self._get_headers())

            logger.info("[CREATIVE_SYNC] Записываю %d строк данных...", len(rows))
            if rows:
                worksheet.append_rows(rows)

            logger.info(
                "✅ [CREATIVE_SYNC] Успешно синхронизировано %d заявок", len(rows)
            )
            return len(rows)

        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:
                logger.error(
                    "[CREATIVE_SYNC] Превышен лимит запросов к Google API (429). "
                    "Попробуйте позже."
                )
            else:
                logger.error(
                    "[CREATIVE_SYNC] Ошибка Google Sheets API: %s",
                    e,
                    exc_info=True,
                )
            raise
        except Exception as e:
            logger.error(
                "[CREATIVE_SYNC] Неожиданная ошибка при синхронизации: %s",
                e,
                exc_info=True,
            )
            raise
