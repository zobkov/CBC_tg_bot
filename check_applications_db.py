#!/usr/bin/env python3
"""
Скрипт для проверки данных в БД заявок
"""
import asyncio
import logging
from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='#%(levelname)-8s [%(asctime)s] - %(filename)s:%(lineno)d - %(name)s:%(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_applications_db():
    """Проверяет данные в БД заявок"""
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        # Подключаемся к БД заявок
        pool = await get_pg_pool(
            db_name=config.db_applications.database,
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password
        )
        
        async with pool.connection() as conn:
            # Проверяем структуру таблицы applications
            cursor = await conn.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'applications' 
                ORDER BY ordinal_position;
            """)
            
            columns = await cursor.fetchall()
            logger.info("Структура таблицы applications:")
            for col in columns:
                logger.info(f"  {col[0]} | {col[1]} | nullable: {col[2]} | default: {col[3]}")
            
            # Проверяем данные в таблице (основные поля, без статуса)
            cursor = await conn.execute("""
                SELECT user_id, full_name, university, course, phone, email, 
                       telegram_username, how_found_kbk,
                       department_1, position_1,
                       department_2, position_2,
                       department_3, position_3,
                       created, updated
                FROM applications
                ORDER BY created DESC;
            """)
            
            applications = await cursor.fetchall()
            logger.info(f"\nВсего заявок: {len(applications)}")
            
            for i, app in enumerate(applications, 1):
                logger.info(f"\nЗаявка {i}:")
                logger.info(f"  User ID: {app[0]}")
                logger.info(f"  Full Name: {app[1]}")
                logger.info(f"  University: {app[2]}")
                logger.info(f"  Course: {app[3]}")
                logger.info(f"  Phone: {app[4]}")
                logger.info(f"  Email: {app[5]}")
                logger.info(f"  Telegram Username: {app[6]}")
                logger.info(f"  How Found KBK: {app[7]}")
                logger.info(f"  Priority 1: {app[8]} / {app[9]}")
                logger.info(f"  Priority 2: {app[10]} / {app[11]}")
                logger.info(f"  Priority 3: {app[12]} / {app[13]}")
                logger.info(f"  Created: {app[14]}")
                logger.info(f"  Updated: {app[15]}")

            # Дополнительно: обзор по таблице users
            cursor = await conn.execute("""
                SELECT submission_status, COUNT(*)
                FROM users
                GROUP BY submission_status
                ORDER BY submission_status;
            """)
            groups = await cursor.fetchall()
            logger.info("\nПользователи по статусам отправки заявки:")
            for status, cnt in groups:
                logger.info(f"  {status}: {cnt}")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке БД заявок: {e}")

if __name__ == "__main__":
    asyncio.run(check_applications_db())
