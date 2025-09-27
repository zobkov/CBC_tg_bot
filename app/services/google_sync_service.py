"""
Сервис для синхронизации данных одобренных заявок с Google Sheets
"""
import logging
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials
import asyncio
import time
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
                    
                    # Получаем все существующие данные для сравнения
                    all_values = worksheet.get_all_records()
                    existing_data = {}
                    
                    # Создаем индекс существующих записей по ID телеграма
                    for i, record in enumerate(all_values):
                        user_id = str(record.get('ID', '')).strip()
                        position = str(record.get('Вакансия', '')).strip()
                        if user_id and position:
                            key = f"{user_id}_{position}"
                            existing_data[key] = {
                                'row_index': i + 2,  # +2 потому что нумерация с 1 + заголовок
                                'comment': record.get('Комментарий', ''),
                                'rating': record.get('Оценка', ''),
                                'task_submitted': record.get('ТЗ сдано', '')
                            }
                    
                    logger.info(f"📋 Найдено {len(existing_data)} существующих записей в листе {sheet_name}")
                    
                    updated_count = 0
                    added_count = 0
                    
                    # Подготавливаем данные для batch-операций
                    rows_to_add = []
                    batch_updates = []
                    
                    # Обрабатываем каждую заявку
                    for app in apps:
                        # Определяем название подотдела
                        subdept_display = ""
                        if app['subdepartment']:
                            subdept_display = self._get_subdepartment_display_name(app['subdepartment'])
                        
                        user_id = str(app['user_id'])
                        position = app['position']
                        key = f"{user_id}_{position}"
                        task_submitted_str = 'True' if app['task_submitted'] else 'False'
                        
                        if key in existing_data:
                            # Проверяем существующую запись на необходимость обновления
                            existing_record = existing_data[key]
                            row_index = existing_record['row_index']
                            
                            # Проверяем, нужно ли обновить статус ТЗ
                            if existing_record['task_submitted'] != task_submitted_str:
                                batch_updates.append({
                                    'range': f'F{row_index}',  # Колонка "ТЗ сдано"
                                    'values': [[task_submitted_str]]
                                })
                                logger.debug(f"🔄 Запланировано обновление статуса ТЗ для {user_id} в позиции {position}")
                                updated_count += 1
                        else:
                            # Добавляем новую запись в batch
                            new_row = [
                                user_id,              # ID
                                app['username'],       # Username
                                app['full_name'],      # ФИО
                                subdept_display,       # Подотдел
                                position,              # Вакансия
                                task_submitted_str,    # ТЗ сдано
                                '',                    # Комментарий (пустой)
                                ''                     # Оценка (пустая)
                            ]
                            rows_to_add.append(new_row)
                            logger.debug(f"➕ Запланировано добавление записи для {user_id} в позиции {position}")
                            added_count += 1
                    
                    # Выполняем batch-обновления
                    if batch_updates:
                        try:
                            logger.info(f"🔄 Выполняем {len(batch_updates)} batch-обновлений...")
                            worksheet.batch_update(batch_updates)
                            logger.info(f"✅ Batch-обновления выполнены успешно")
                            time.sleep(1)  # Задержка после batch операции
                        except Exception as api_error:
                            if "429" in str(api_error) or "Quota exceeded" in str(api_error):
                                logger.warning(f"⚠️ Превышена квота API при batch-обновлении, ждем 60 секунд...")
                                time.sleep(60)
                                worksheet.batch_update(batch_updates)
                            else:
                                logger.error(f"Ошибка при batch-обновлении: {api_error}")
                                # Откатываемся на обычные обновления
                                for update in batch_updates:
                                    try:
                                        range_cell = update['range']
                                        value = update['values'][0][0]
                                        worksheet.update(range_cell, [[value]])
                                        time.sleep(0.2)
                                    except Exception as e:
                                        logger.error(f"Ошибка обновления {range_cell}: {e}")
                    
                    # Выполняем добавление новых записей
                    if rows_to_add:
                        try:
                            logger.info(f"➕ Добавляем {len(rows_to_add)} новых записей...")
                            worksheet.append_rows(rows_to_add)
                            logger.info(f"✅ Новые записи добавлены успешно")
                            time.sleep(1)  # Задержка после добавления
                        except Exception as api_error:
                            if "429" in str(api_error) or "Quota exceeded" in str(api_error):
                                logger.warning(f"⚠️ Превышена квота API при добавлении записей, ждем 60 секунд...")
                                time.sleep(60)
                                worksheet.append_rows(rows_to_add)
                            else:
                                logger.error(f"Ошибка при добавлении записей: {api_error}")
                                # Откатываемся на добавление по одной записи
                                for row in rows_to_add:
                                    try:
                                        worksheet.append_row(row)
                                        time.sleep(0.2)
                                    except Exception as e:
                                        logger.error(f"Ошибка добавления записи: {e}")
                    
                    logger.info(f"✅ Лист {sheet_name}: обновлено {updated_count} записей, добавлено {added_count} записей")
                    sync_stats[sheet_name] = updated_count + added_count
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки листа {sheet_name}: {e}")
                    sync_stats[sheet_name] = 0
                
                # Добавляем задержку между обработкой отделов
                time.sleep(2)
            
            total_changes = sum(sync_stats.values())
            logger.info(f"🎉 Синхронизация завершена. Всего изменений: {total_changes}")
            logger.info(f"📊 Статистика изменений по отделам: {sync_stats}")
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