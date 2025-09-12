#!/usr/bin/env python3
"""
Скрипт для заполнения таблицы evaluated_applications на основе CSV файла
с результатами второй стадии отбора
"""
import asyncio
import psycopg
import csv
import logging
import sys
import os
from config.config import load_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='#%(levelname)-8s [%(asctime)s] - %(filename)s:%(lineno)d - %(name)s:%(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def populate_evaluated_applications(csv_file_path: str):
    """
    Заполняет таблицу evaluated_applications данными из CSV файла
    
    Args:
        csv_file_path: Путь к CSV файлу с данными
        
    CSV должен содержать столбцы:
    user_id, username, full_name, dep_1, subdep_1, pos_1, accepted_1,
    dep_2, subdep_2, pos_2, accepted_2, dep_3, subdep_3, pos_3, accepted_3
    """
    logger.info("Загрузка конфигурации")
    config = load_config()
    
    # Проверяем существование файла
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV файл не найден: {csv_file_path}")
        return False
    
    # Читаем CSV файл
    try:
        logger.info(f"Чтение CSV файла: {csv_file_path}")
        
        # Читаем CSV и преобразуем в список словарей
        csv_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            csv_data = list(reader)
            
        logger.info(f"Загружено {len(csv_data)} записей из CSV")
        
        # Проверяем наличие необходимых столбцов
        if not csv_data:
            logger.error("CSV файл пустой")
            return False
            
        required_columns = ['user_id', 'accepted_1', 'accepted_2', 'accepted_3']
        available_columns = csv_data[0].keys()
        missing_columns = [col for col in required_columns if col not in available_columns]
        if missing_columns:
            logger.error(f"Отсутствуют необходимые столбцы в CSV: {missing_columns}")
            return False
            
        logger.info(f"Столбцы CSV: {list(available_columns)}")
        
    except Exception as e:
        logger.error(f"Ошибка чтения CSV файла: {e}")
        return False
    
    # Подключение к базе данных заявок
    connection_string = f"postgresql://{config.db_applications.user}:{config.db_applications.password}@{config.db_applications.host}:{config.db_applications.port}/{config.db_applications.database}"
    
    logger.info("Подключение к базе данных заявок")
    async with await psycopg.AsyncConnection.connect(connection_string) as conn:
        async with conn.cursor() as cur:
            # Проверяем, что таблица evaluated_applications существует
            await cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'evaluated_applications'
                )
            """)
            table_exists = (await cur.fetchone())[0]
            
            if not table_exists:
                logger.error("Таблица evaluated_applications не существует. Запустите миграцию 008_create_evaluated_applications_table.sql")
                return False
            
            # Очищаем таблицу перед заполнением (опционально)
            logger.info("Очистка таблицы evaluated_applications")
            await cur.execute("DELETE FROM evaluated_applications")
            
            # Подготавливаем данные для вставки
            successful_inserts = 0
            failed_inserts = 0
            
            for index, row in enumerate(csv_data):
                try:
                    user_id = int(row['user_id'])
                    
                    # Преобразуем строковые значения в boolean
                    def to_bool(value):
                        if isinstance(value, str):
                            return value.lower() in ('true', '1', 'yes', 'да', 'y')
                        return bool(value)
                    
                    accepted_1 = to_bool(row['accepted_1'])
                    accepted_2 = to_bool(row['accepted_2'])
                    accepted_3 = to_bool(row['accepted_3'])
                    
                    # Проверяем, что пользователь существует в таблице users
                    await cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                    user_exists = await cur.fetchone()
                    
                    if not user_exists:
                        logger.warning(f"Пользователь {user_id} не найден в таблице users, пропускаем")
                        failed_inserts += 1
                        continue
                    
                    # Вставляем запись в evaluated_applications
                    await cur.execute("""
                        INSERT INTO evaluated_applications (user_id, accepted_1, accepted_2, accepted_3)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET 
                            accepted_1 = EXCLUDED.accepted_1,
                            accepted_2 = EXCLUDED.accepted_2,
                            accepted_3 = EXCLUDED.accepted_3,
                            updated = NOW()
                    """, (user_id, accepted_1, accepted_2, accepted_3))
                    
                    successful_inserts += 1
                    
                    if successful_inserts % 100 == 0:
                        logger.info(f"Обработано {successful_inserts} записей")
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки строки {index}: {e}")
                    failed_inserts += 1
                    continue
            
            # Фиксируем транзакцию
            await conn.commit()
            
            logger.info(f"Заполнение completed:")
            logger.info(f"  Успешно вставлено: {successful_inserts}")
            logger.info(f"  Ошибок: {failed_inserts}")
            
            # Проверяем итоговое количество записей
            await cur.execute("SELECT COUNT(*) FROM evaluated_applications")
            total_count = (await cur.fetchone())[0]
            logger.info(f"  Итого записей в таблице: {total_count}")
            
    return True


async def main():
    if len(sys.argv) != 2:
        print("Использование: python populate_evaluated_applications.py <путь_к_csv_файлу>")
        print("Пример: python populate_evaluated_applications.py data/second_stage_results.csv")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    success = await populate_evaluated_applications(csv_file_path)
    
    if success:
        logger.info("Скрипт выполнен успешно")
        sys.exit(0)
    else:
        logger.error("Скрипт завершился с ошибкой")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())