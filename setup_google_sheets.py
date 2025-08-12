#!/usr/bin/env python3
"""
Скрипт для настройки Google Sheets с правильными заголовками и тестовыми данными
"""

import asyncio
import logging
from datetime import datetime
from app.services.google_services import GoogleServicesManager
from config.config import load_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def setup_sheets():
    """Настройка Google Sheets с правильными заголовками и тестовыми данными"""
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        if not config.google:
            logger.error("❌ Google конфигурация не найдена")
            return
        
        # Создаем менеджер Google сервисов
        google_manager = GoogleServicesManager(
            credentials_path=config.google.credentials_path,
            spreadsheet_id=config.google.spreadsheet_id,
            drive_folder_id=config.google.drive_folder_id,
            enable_drive=config.google.enable_drive
        )
        
        logger.info("✅ Google Services Manager инициализирован")
        
        # Открываем таблицу
        spreadsheet = google_manager.gc.open(google_manager.spreadsheet_name)
        logger.info(f"📋 Открыта таблица: {google_manager.spreadsheet_name}")
        
        # Получаем или создаем лист Applications
        worksheet_name = "Applications"
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"✅ Лист {worksheet_name} найден")
            
            # Очищаем существующий лист
            logger.info("🧹 Очищаем существующий лист...")
            worksheet.clear()
            
        except Exception:
            logger.info(f"📄 Лист {worksheet_name} не найден, создаем новый...")
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=25)
        
        # Правильные заголовки согласно новой системе приоритетов
        headers = [
            'Timestamp',           # A
            'User ID',             # B
            'Username',            # C
            'Full Name',           # D
            'University',          # E
            'Course',              # F
            'Phone',               # G
            'Email',               # H
            'How Found KBK',       # I
            'Previous Department', # J
            'Department 1',        # K
            'Position 1',          # L
            'Department 2',        # M
            'Position 2',          # N
            'Department 3',        # O
            'Position 3',          # P
            'Priorities',          # Q
            'Experience',          # R
            'Motivation',          # S
            'Status',              # T
            'Resume Local Path',   # U
            'Resume Google Drive URL'  # V
        ]
        
        logger.info("📋 Добавляем заголовки...")
        worksheet.append_row(headers)
        
        # Добавляем тестовые данные согласно новой системе
        test_data = [
            [
                datetime.now().isoformat(),                    # Timestamp
                '123456789',                                   # User ID
                'test_user',                                   # Username
                'Иванов Иван Иванович',                       # Full Name
                'МГУ имени М.В. Ломоносова',                  # University
                '3',                                           # Course
                '+7-999-123-45-67',                           # Phone
                'test@example.com',                            # Email
                'Социальные сети, Друзья',                    # How Found KBK
                '',                                            # Previous Department
                'Отдел технологий',                           # Department 1
                'Python разработчик',                         # Position 1
                'Отдел дизайна',                              # Department 2
                'UI/UX дизайнер',                             # Position 2
                'Отдел менеджмента',                          # Department 3
                'Проект-менеджер',                            # Position 3
                '1) Отдел технологий - Python разработчик; 2) Отдел дизайна - UI/UX дизайнер; 3) Отдел менеджмента - Проект-менеджер',  # Priorities
                'Опыт работы с Python 2 года',               # Experience
                'Хочу развиваться в IT',                      # Motivation
                'submitted',                                   # Status
                'app/storage/resumes/resume_123456789.pdf',   # Resume Local Path
                'https://drive.google.com/file/d/example123/view'  # Resume Google Drive URL
            ],
            [
                datetime.now().isoformat(),                    # Timestamp
                '987654321',                                   # User ID
                'student_user',                                # Username
                'Петрова Анна Сергеевна',                     # Full Name
                'СПБГУ',                                       # University
                '2',                                           # Course
                '+7-912-345-67-89',                           # Phone
                'anna.petrova@student.spbu.ru',               # Email
                'Университет, Социальные сети',               # How Found KBK
                '',                                            # Previous Department
                'Отдел маркетинга',                           # Department 1
                'SMM-специалист',                             # Position 1
                'Отдел дизайна',                              # Department 2
                'Графический дизайнер',                       # Position 2
                '',                                            # Department 3
                '',                                            # Position 3
                '1) Отдел маркетинга - SMM-специалист; 2) Отдел дизайна - Графический дизайнер',  # Priorities
                'Ведение соц.сетей для кафе, фотография',    # Experience
                'Интересно попробовать себя в маркетинге',    # Motivation
                'submitted',                                   # Status
                'app/storage/resumes/resume_987654321.pdf',   # Resume Local Path
                ''                                             # Resume Google Drive URL
            ]
        ]
        
        logger.info("📝 Добавляем тестовые данные...")
        for i, row in enumerate(test_data, 1):
            worksheet.append_row(row)
            logger.info(f"✅ Добавлена тестовая запись {i}")
        
        # Форматируем заголовки (делаем их жирными)
        logger.info("🎨 Форматируем заголовки...")
        try:
            worksheet.format('A1:V1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            logger.info("✅ Заголовки отформатированы")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отформатировать заголовки: {e}")
        
        # Автоматически подгоняем ширину колонок
        logger.info("📏 Настраиваем ширину колонок...")
        try:
            # Устанавливаем ширину колонок
            requests = [
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': worksheet.id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,  # A
                            'endIndex': 22    # V
                        },
                        'properties': {
                            'pixelSize': 150
                        },
                        'fields': 'pixelSize'
                    }
                }
            ]
            
            spreadsheet.batch_update({'requests': requests})
            logger.info("✅ Ширина колонок настроена")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось настроить ширину колонок: {e}")
        
        logger.info("🎉 Google Sheets успешно настроен!")
        logger.info(f"🔗 Ссылка на таблицу: https://docs.google.com/spreadsheets/d/{config.google.spreadsheet_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Google Sheets: {e}")
        return False


async def test_application_export():
    """Тест экспорта заявки в Google Sheets"""
    try:
        config = load_config()
        
        google_manager = GoogleServicesManager(
            credentials_path=config.google.credentials_path,
            spreadsheet_id=config.google.spreadsheet_id,
            drive_folder_id=config.google.drive_folder_id,
            enable_drive=config.google.enable_drive
        )
        
        # Тестовые данные заявки в формате системы приоритетов
        test_application = {
            'timestamp': datetime.now().isoformat(),
            'user_id': '555666777',
            'username': 'priority_test_user',
            'full_name': 'Тестов Приоритет Системович',
            'university': 'Тестовый Технический Университет',
            'course': '4',
            'phone': '+7-555-666-77-88',
            'email': 'priority.test@example.com',
            'how_found_kbk': 'Тестирование системы приоритетов',
            'previous_department': '',
            'department_1': 'Отдел разработки',
            'position_1': 'Backend разработчик',
            'department_2': 'Отдел аналитики',
            'position_2': 'Бизнес-аналитик',
            'department_3': 'Отдел QA',
            'position_3': 'Тестировщик',
            'priorities': '1) Отдел разработки - Backend разработчик; 2) Отдел аналитики - Бизнес-аналитик; 3) Отдел QA - Тестировщик',
            'experience': 'Опыт в тестировании системы приоритетов',
            'motivation': 'Хочу проверить работу новой системы приоритетов',
            'status': 'submitted',
            'resume_local_path': 'app/storage/resumes/priority_test.pdf',
            'resume_google_drive_url': 'https://drive.google.com/file/d/test_priority/view'
        }
        
        logger.info("🧪 Тестируем экспорт заявки с системой приоритетов...")
        success = await google_manager.add_application_to_sheet(test_application)
        
        if success:
            logger.info("✅ Тест экспорта прошел успешно!")
        else:
            logger.error("❌ Тест экспорта не удался!")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста экспорта: {e}")
        return False


async def main():
    """Главная функция"""
    logger.info("🚀 Запуск настройки Google Sheets...")
    
    # Настраиваем Google Sheets
    setup_success = await setup_sheets()
    
    if setup_success:
        logger.info("✅ Настройка Google Sheets завершена")
        
        # Тестируем экспорт
        logger.info("🧪 Запуск теста экспорта...")
        test_success = await test_application_export()
        
        if test_success:
            logger.info("🎉 Все тесты прошли успешно!")
        else:
            logger.error("❌ Тесты не прошли")
    else:
        logger.error("❌ Настройка Google Sheets не удалась")


if __name__ == "__main__":
    asyncio.run(main())
