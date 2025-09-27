#!/usr/bin/env python3
"""
Скрипт для сравнения данных в таблице evaluated_applications с CSV файлом
и вывода пользователей, которые отсутствуют в базе данных
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


async def compare_evaluated_applications(csv_file_path: str):
    """
    Сравнивает данные в таблице evaluated_applications с CSV файлом
    и выводит пользователей, которые отсутствуют в базе данных
    
    Args:
        csv_file_path: Путь к CSV файлу с данными
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
        
        # Читаем CSV и извлекаем user_id из всех записей
        csv_user_ids = set()
        csv_data = {}
        duplicate_ids = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, 1):
                try:
                    user_id = int(row['user_id'])
                    
                    # Отслеживаем дублирующиеся ID
                    if user_id in csv_user_ids:
                        duplicate_ids.append((user_id, row_num))
                        logger.warning(f"Дублирующийся user_id {user_id} в строке {row_num}")
                    
                    csv_user_ids.add(user_id)
                    # Сохраняем данные только первого вхождения пользователя
                    if user_id not in csv_data:
                        csv_data[user_id] = {
                            'username': row.get('username', ''),
                            'full_name': row.get('full_name', ''),
                            'accepted_1': row.get('accepted_1', ''),
                            'accepted_2': row.get('accepted_2', ''),
                            'accepted_3': row.get('accepted_3', ''),
                            'row_num': row_num
                        }
                except ValueError:
                    logger.warning(f"Некорректный user_id в строке {row_num}: {row}")
                    continue
            
        logger.info(f"Загружено {len(csv_user_ids)} уникальных пользователей из CSV")
        if duplicate_ids:
            logger.warning(f"Найдено {len(duplicate_ids)} дублирующихся записей: {duplicate_ids}")
        
    except Exception as e:
        logger.error(f"Ошибка чтения CSV файла: {e}")
        return False
    
    # Подключение к базе данных заявок
    connection_string = f"postgresql://{config.db_applications.user}:{config.db_applications.password}@{config.db_applications.host}:{config.db_applications.port}/{config.db_applications.database}"
    
    logger.info("Подключение к базе данных заявок")
    async with await psycopg.AsyncConnection.connect(connection_string) as conn:
        async with conn.cursor() as cur:
            # Получаем все user_id из evaluated_applications
            await cur.execute("SELECT user_id FROM evaluated_applications")
            db_user_ids = set(row[0] for row in await cur.fetchall())
            logger.info(f"В таблице evaluated_applications найдено {len(db_user_ids)} пользователей")
            
            # Получаем все user_id из таблицы users для проверки
            await cur.execute("SELECT user_id FROM users")
            users_table_ids = set(row[0] for row in await cur.fetchall())
            logger.info(f"В таблице users найдено {len(users_table_ids)} пользователей")
            
            # Находим пользователей из CSV, которых нет в evaluated_applications
            missing_in_evaluated = csv_user_ids - db_user_ids
            
            # Находим пользователей из CSV, которых нет в таблице users
            missing_in_users = csv_user_ids - users_table_ids
            
            # Находим пользователей, которые есть в users, но отсутствуют в evaluated_applications
            missing_but_in_users = missing_in_evaluated - missing_in_users
            
            print("\n" + "="*80)
            print("РЕЗУЛЬТАТЫ СРАВНЕНИЯ")
            print("="*80)
            
            print(f"\nОбщая статистика:")
            print(f"  Пользователей в CSV файле: {len(csv_user_ids)}")
            print(f"  Пользователей в evaluated_applications: {len(db_user_ids)}")
            print(f"  Пользователей в таблице users: {len(users_table_ids)}")
            
            print(f"\nОтсутствуют в evaluated_applications (всего): {len(missing_in_evaluated)}")
            print(f"Из них:")
            print(f"  - Есть в таблице users: {len(missing_but_in_users)}")
            print(f"  - Отсутствуют в таблице users: {len(missing_in_users)}")
            
            if missing_in_users:
                print(f"\n⚠️  ПОЛЬЗОВАТЕЛИ, ОТСУТСТВУЮЩИЕ В ТАБЛИЦЕ USERS:")
                print("-" * 60)
                for user_id in sorted(missing_in_users):
                    user_data = csv_data[user_id]
                    print(f"  {user_id:>12} | {user_data['username']:<20} | {user_data['full_name']}")
            
            if missing_but_in_users:
                print(f"\n✅ ПОЛЬЗОВАТЕЛИ ДЛЯ ДОБАВЛЕНИЯ В EVALUATED_APPLICATIONS:")
                print("-" * 70)
                print(f"{'User ID':>12} | {'Username':^20} | {'Full Name':^30} | {'Results'}")
                print("-" * 70)
                
                for user_id in sorted(missing_but_in_users):
                    user_data = csv_data[user_id]
                    results = f"{user_data['accepted_1']}/{user_data['accepted_2']}/{user_data['accepted_3']}"
                    print(f"  {user_id:>12} | {user_data['username']:^20} | {user_data['full_name']:<30} | {results}")
            
            if not missing_in_evaluated:
                print(f"\n✅ Все пользователи из CSV уже присутствуют в evaluated_applications")
            
            # Проверяем пользователей в evaluated_applications, которых нет в CSV
            extra_in_db = db_user_ids - csv_user_ids
            if extra_in_db:
                print(f"\n📋 ПОЛЬЗОВАТЕЛИ В EVALUATED_APPLICATIONS, НО НЕ В CSV ({len(extra_in_db)}):")
                print("-" * 40)
                for user_id in sorted(extra_in_db):
                    print(f"  {user_id}")
            
            print("\n" + "="*80)
            
            return {
                'csv_total': len(csv_user_ids),
                'db_total': len(db_user_ids),
                'missing_in_evaluated': list(missing_in_evaluated),
                'missing_in_users': list(missing_in_users),
                'can_add_to_evaluated': list(missing_but_in_users),
                'extra_in_db': list(extra_in_db)
            }


async def main():
    if len(sys.argv) != 2:
        print("Использование: python compare_evaluated_applications.py <путь_к_csv_файлу>")
        print("Пример: python compare_evaluated_applications.py 'Заявки КБК26 - Оцененные заявки для выгрузки (2).csv'")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    result = await compare_evaluated_applications(csv_file_path)
    
    if result:
        logger.info("Сравнение выполнено успешно")
        sys.exit(0)
    else:
        logger.error("Ошибка при выполнении сравнения")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())