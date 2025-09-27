"""
Сервис для синхронизации данных одобренных заявок с Google Sheets
"""
import logging
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleSyncService:
    """Сервис для синхронизации данных одобренных заявок с Google Sheets"""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Инициализация сервиса синхронизации
        
        Args:
            credentials_path: Путь к файлу с учетными данными сервисного аккаунта
            spreadsheet_id: ID Google Таблицы
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        
        # Области доступа
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        
        # Маппинг отделов на листы в Google Sheets
        self.department_sheets = {
            'Отдел логистики и ИТ': 'Logistics',
            'Выставочный отдел': 'Exhibition', 
            'Отдел SMM&PR': 'SMMPR',
            'Отдел дизайна': 'Design',
            'Отдел партнёров': 'Partners',
            'Отдел программы': 'Program',
            'Творческий отдел': 'Art'
        }
        
        self._setup_service()
    
    def _setup_service(self):
        """Настройка Google Sheets API"""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.scopes
            )
            
            self.gc = gspread.authorize(credentials)
            logger.info("✅ Google Sheets API для синхронизации настроен")
            
        except Exception as e:
            logger.error(f"Ошибка настройки Google Sheets API: {e}")
            raise
    
    async def get_approved_applications_data(self, db_pool) -> List[Dict[str, Any]]:
        """
        Получает данные одобренных заявок из базы данных
        
        Args:
            db_pool: Пул соединений с базой данных applications
            
        Returns:
            List[Dict]: Список данных одобренных заявок
        """
        try:
            async with db_pool.connection() as conn:
                # Запрос для получения всех одобренных заявок
                query = """
                SELECT 
                    u.user_id,
                    a.telegram_username,
                    a.full_name,
                    a.department_1,
                    a.position_1,
                    a.subdepartment_1,
                    a.department_2,
                    a.position_2,
                    a.subdepartment_2,
                    a.department_3,
                    a.position_3,
                    a.subdepartment_3,
                    u.task_1_submitted,
                    u.task_2_submitted,
                    u.task_3_submitted,
                    ea.accepted_1,
                    ea.accepted_2,
                    ea.accepted_3
                FROM users u
                JOIN applications a ON u.user_id = a.user_id
                JOIN evaluated_applications ea ON u.user_id = ea.user_id
                WHERE (ea.accepted_1 = true OR ea.accepted_2 = true OR ea.accepted_3 = true)
                AND u.submission_status = 'submitted'
                ORDER BY u.user_id;
                """
                
                async with conn.cursor() as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()
                    
                    # Получаем имена колонок
                    column_names = [desc.name for desc in cursor.description]
                    
                    # Конвертируем в список словарей
                    result_rows = []
                    for row in rows:
                        result_rows.append(dict(zip(column_names, row)))
                
                applications_data = []
                for row in result_rows:
                    # Создаем записи для каждой одобренной вакансии
                    user_data = {
                        'user_id': row['user_id'],
                        'username': row['telegram_username'] or '',
                        'full_name': row['full_name'] or '',
                        'task_1_submitted': row['task_1_submitted'],
                        'task_2_submitted': row['task_2_submitted'],
                        'task_3_submitted': row['task_3_submitted'],
                    }
                    
                    # Добавляем запись для каждой одобренной позиции
                    if row['accepted_1'] and row['department_1']:
                        applications_data.append({
                            **user_data,
                            'department': row['department_1'],
                            'position': row['position_1'] or '',
                            'subdepartment': row['subdepartment_1'] or '',
                            'task_submitted': row['task_1_submitted'],
                            'priority': 1
                        })
                    
                    if row['accepted_2'] and row['department_2']:
                        applications_data.append({
                            **user_data,
                            'department': row['department_2'],
                            'position': row['position_2'] or '',
                            'subdepartment': row['subdepartment_2'] or '',
                            'task_submitted': row['task_2_submitted'],
                            'priority': 2
                        })
                    
                    if row['accepted_3'] and row['department_3']:
                        applications_data.append({
                            **user_data,
                            'department': row['department_3'],
                            'position': row['position_3'] or '',
                            'subdepartment': row['subdepartment_3'] or '',
                            'task_submitted': row['task_3_submitted'],
                            'priority': 3
                        })
                
                logger.info(f"Получено {len(applications_data)} записей одобренных заявок")
                return applications_data
                
        except Exception as e:
            logger.error(f"Ошибка получения данных одобренных заявок: {e}")
            return []
    
    def _get_department_display_name(self, department_key: str) -> str:
        """Получает отображаемое имя отдела"""
        department_names = {
            'logistics_it': 'Отдел логистики и ИТ',
            'exhibition': 'Выставочный отдел',
            'smm_pr': 'Отдел SMM&PR',
            'design': 'Отдел дизайна',
            'partners': 'Отдел партнёров',
            'program': 'Отдел программы',
            'creative': 'Творческий отдел'
        }
        return department_names.get(department_key, department_key)
    
    def _get_subdepartment_display_name(self, subdept_key: str) -> str:
        """Получает отображаемое имя под-отдела"""
        subdept_names = {
            'stage': 'Сценическое направление',
            'booth': 'Стендовая сессия',
            'social': 'Социальные сети на русском и китайском',
            'media': 'Медиа-шоу'
        }
        return subdept_names.get(subdept_key, subdept_key)
    
    async def sync_to_google_sheets(self, applications_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Синхронизирует данные одобренных заявок с Google Sheets
        
        Args:
            applications_data: Список данных одобренных заявок
            
        Returns:
            Dict[str, int]: Статистика синхронизации по отделам
        """
        try:
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            
            # Группируем данные по отделам
            department_data = {}
            for app in applications_data:
                dept_key = app['department']
                if dept_key not in department_data:
                    department_data[dept_key] = []
                department_data[dept_key].append(app)
            
            sync_stats = {}
            
            # Обрабатываем каждый отдел
            for dept_key, apps in department_data.items():
                sheet_name = self.department_sheets.get(dept_key, dept_key)
                
                try:
                    # Получаем или создаем лист
                    try:
                        worksheet = spreadsheet.worksheet(sheet_name)
                        logger.info(f"✅ Найден лист: {sheet_name}")
                    except gspread.WorksheetNotFound:
                        logger.info(f"📄 Создаем новый лист: {sheet_name}")
                        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=8)
                        
                        # Добавляем заголовки
                        headers = ['ID', 'Username', 'ФИО', 'Подотдел', 'Вакансия', 'ТЗ сдано', 'Комментарий', 'Оценка']
                        worksheet.append_row(headers)
                        logger.info(f"✅ Добавлены заголовки для листа {sheet_name}")
                    
                    # Очищаем все данные кроме заголовков
                    if worksheet.row_count > 1:
                        worksheet.delete_rows(2, worksheet.row_count)
                        logger.info(f"🧹 Очищены старые данные в листе {sheet_name}")
                    
                    # Подготавливаем данные для вставки
                    rows_to_insert = []
                    for app in apps:
                        # Определяем название подотдела
                        subdept_display = ""
                        if app['subdepartment']:
                            subdept_display = self._get_subdepartment_display_name(app['subdepartment'])
                        
                        row = [
                            str(app['user_id']),  # ID
                            app['username'],       # Username
                            app['full_name'],      # ФИО
                            subdept_display,       # Подотдел
                            app['position'],       # Вакансия
                            'True' if app['task_submitted'] else 'False',  # ТЗ сдано
                            '',  # Комментарий (пустой)
                            ''   # Оценка (пустая)
                        ]
                        rows_to_insert.append(row)
                    
                    # Вставляем все данные одним запросом
                    if rows_to_insert:
                        worksheet.append_rows(rows_to_insert)
                        logger.info(f"✅ Добавлено {len(rows_to_insert)} записей в лист {sheet_name}")
                    
                    sync_stats[sheet_name] = len(rows_to_insert)
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки листа {sheet_name}: {e}")
                    sync_stats[sheet_name] = 0
            
            logger.info(f"🎉 Синхронизация завершена. Статистика: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации с Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def sync_approved_applications(self, db_pool) -> Dict[str, int]:
        """
        Полная синхронизация одобренных заявок
        
        Args:
            db_pool: Пул соединений с базой данных
            
        Returns:
            Dict[str, int]: Статистика синхронизации
        """
        try:
            logger.info("🚀 Начинаем синхронизацию одобренных заявок с Google Sheets")
            
            # Получаем данные одобренных заявок
            applications_data = await self.get_approved_applications_data(db_pool)
            
            if not applications_data:
                logger.warning("⚠️ Нет данных для синхронизации")
                return {}
            
            # Синхронизируем с Google Sheets
            sync_stats = await self.sync_to_google_sheets(applications_data)
            
            logger.info(f"✅ Синхронизация завершена успешно: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка полной синхронизации: {e}")
            return {}


async def setup_google_sync_service(credentials_path: str, spreadsheet_id: str) -> Optional[GoogleSyncService]:
    """
    Настройка сервиса синхронизации Google Sheets
    
    Args:
        credentials_path: Путь к файлу учетных данных
        spreadsheet_id: ID Google Таблицы
        
    Returns:
        GoogleSyncService или None в случае ошибки
    """
    try:
        return GoogleSyncService(credentials_path, spreadsheet_id)
    except Exception as e:
        logger.error(f"Ошибка настройки сервиса синхронизации: {e}")
        return None