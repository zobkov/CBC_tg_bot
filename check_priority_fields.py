#!/usr/bin/env python3
"""
Скрипт для проверки полей приоритетов в БД заявок
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

async def check_priority_fields():
    """Проверяет поля приоритетов в БД заявок"""
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
            # Проверяем поля приоритетов в существующих записях
            cursor = await conn.execute("""
                SELECT user_id, full_name, status,
                       -- Старая система
                       department, position,
                       -- Новая система приоритетов
                       department_1, position_1,
                       department_2, position_2,
                       department_3, position_3,
                       created, updated
                FROM applications
                ORDER BY created DESC;
            """)
            
            applications = await cursor.fetchall()
            logger.info(f"🔍 Проверка полей приоритетов в {len(applications)} заявках:")
            
            for i, app in enumerate(applications, 1):
                user_id, full_name, status = app[0], app[1], app[2]
                old_dept, old_pos = app[3], app[4]
                dept1, pos1, dept2, pos2, dept3, pos3 = app[5], app[6], app[7], app[8], app[9], app[10]
                created, updated = app[11], app[12]
                
                logger.info(f"\n📋 Заявка {i} (User ID: {user_id}, {full_name}):")
                logger.info(f"   📅 Создана: {created}")
                logger.info(f"   🔄 Обновлена: {updated}")
                logger.info(f"   📊 Статус: {status}")
                
                # Старая система
                logger.info(f"   🗂️ Старая система:")
                logger.info(f"      Department: {old_dept or 'NULL'}")
                logger.info(f"      Position: {old_pos or 'NULL'}")
                
                # Новая система приоритетов
                logger.info(f"   🎯 Новая система приоритетов:")
                logger.info(f"      1-й приоритет: {dept1 or 'NULL'} - {pos1 or 'NULL'}")
                logger.info(f"      2-й приоритет: {dept2 or 'NULL'} - {pos2 or 'NULL'}")
                logger.info(f"      3-й приоритет: {dept3 or 'NULL'} - {pos3 or 'NULL'}")
                
                # Анализ
                has_old_data = old_dept is not None or old_pos is not None
                has_new_data = any([dept1, pos1, dept2, pos2, dept3, pos3])
                
                if has_old_data and not has_new_data:
                    logger.info(f"   ⚠️  ПРОБЛЕМА: Использует старую систему, приоритеты НЕ заполнены!")
                elif has_new_data and not has_old_data:
                    logger.info(f"   ✅ ОК: Использует новую систему приоритетов")
                elif has_old_data and has_new_data:
                    logger.info(f"   🔄 ПЕРЕХОДНОЕ СОСТОЯНИЕ: Есть данные в обеих системах")
                else:
                    logger.info(f"   ❌ ПУСТО: Нет данных ни в одной из систем")
            
            # Статистика по полям
            cursor = await conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(department) as has_old_dept,
                    COUNT(position) as has_old_pos,
                    COUNT(department_1) as has_dept_1,
                    COUNT(position_1) as has_pos_1,
                    COUNT(department_2) as has_dept_2,
                    COUNT(position_2) as has_pos_2,
                    COUNT(department_3) as has_dept_3,
                    COUNT(position_3) as has_pos_3
                FROM applications;
            """)
            
            stats = await cursor.fetchone()
            total = stats[0]
            
            logger.info(f"\n📊 СТАТИСТИКА ПО ПОЛЯМ:")
            logger.info(f"   📋 Всего заявок: {total}")
            logger.info(f"   🗂️ Старая система:")
            logger.info(f"      - department: {stats[1]}/{total}")
            logger.info(f"      - position: {stats[2]}/{total}")
            logger.info(f"   🎯 Новая система приоритетов:")
            logger.info(f"      - department_1: {stats[3]}/{total}")
            logger.info(f"      - position_1: {stats[4]}/{total}")
            logger.info(f"      - department_2: {stats[5]}/{total}")
            logger.info(f"      - position_2: {stats[6]}/{total}")
            logger.info(f"      - department_3: {stats[7]}/{total}")
            logger.info(f"      - position_3: {stats[8]}/{total}")
            
            if stats[3] == 0 and stats[4] == 0:
                logger.error(f"\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА:")
                logger.error(f"   Ни одна заявка не использует новую систему приоритетов!")
                logger.error(f"   Код сохранения НЕ обновлен для работы с новыми полями.")
            elif stats[1] > 0 and stats[3] > 0:
                logger.info(f"\n🔄 СОСТОЯНИЕ МИГРАЦИИ:")
                logger.info(f"   Система в переходном состоянии - есть данные в обеих системах")
            else:
                logger.info(f"\n✅ СИСТЕМА ОБНОВЛЕНА:")
                logger.info(f"   Используется только новая система приоритетов")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке БД заявок: {e}")

if __name__ == "__main__":
    asyncio.run(check_priority_fields())
