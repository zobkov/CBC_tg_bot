#!/usr/bin/env python3
"""
Быстрый скрипт для получения текущей статистики КБК.
Выводит основные метрики в консоль и сохраняет краткий CSV файл.
"""
import asyncio
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
import psycopg

from config.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_quick_stats():
    """Получает быструю сводку по основным метрикам"""
    config = load_config()
    
    connection_string = (
        f"postgresql://{config.db_applications.user}:"
        f"{config.db_applications.password}@"
        f"{config.db_applications.host}:"
        f"{config.db_applications.port}/"
        f"{config.db_applications.database}"
    )
    
    connection = await psycopg.AsyncConnection.connect(connection_string)
    
    try:
        # Основная статистика
        cursor = await connection.execute("""
            SELECT 
                COUNT(DISTINCT u.user_id) as total_users,
                COUNT(DISTINCT u.user_id) FILTER (WHERE u.is_blocked = TRUE) as blocked_users,
                COUNT(DISTINCT u.user_id) FILTER (WHERE u.submission_status = 'not_submitted') as not_submitted,
                COUNT(DISTINCT u.user_id) FILTER (WHERE u.submission_status = 'submitted') as submitted,
                COUNT(DISTINCT a.user_id) as started_applications,
                COUNT(DISTINCT a.user_id) FILTER (WHERE a.full_name IS NOT NULL) as filled_applications
            FROM users u
            LEFT JOIN applications a ON u.user_id = a.user_id;
        """)
        
        row = await cursor.fetchone()
        
        stats = {
            'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            'total_users': row[0] or 0,
            'blocked_users': row[1] or 0,
            'active_users': (row[0] or 0) - (row[1] or 0),
            'not_submitted': row[2] or 0,
            'submitted': row[3] or 0,
            'started_applications': row[4] or 0,
            'filled_applications': row[5] or 0
        }
        
        # Статистика за последние 7 дней
        cursor = await connection.execute("""
            SELECT 
                COUNT(DISTINCT u.user_id) as new_users_7d,
                COUNT(DISTINCT a.user_id) as new_applications_7d
            FROM users u
            LEFT JOIN applications a ON u.user_id = a.user_id
            WHERE u.created >= CURRENT_DATE - INTERVAL '7 days';
        """)
        
        row = await cursor.fetchone()
        stats['new_users_7d'] = row[0] or 0
        stats['new_applications_7d'] = row[1] or 0
        
        # Статистика за сегодня
        cursor = await connection.execute("""
            SELECT 
                COUNT(DISTINCT u.user_id) as new_users_today,
                COUNT(DISTINCT a.user_id) as new_applications_today
            FROM users u
            LEFT JOIN applications a ON u.user_id = a.user_id
            WHERE DATE(u.created) = CURRENT_DATE;
        """)
        
        row = await cursor.fetchone()
        stats['new_users_today'] = row[0] or 0
        stats['new_applications_today'] = row[1] or 0
        
        # Выводим в консоль
        print("\n" + "="*50)
        print("КБК - ТЕКУЩАЯ СТАТИСТИКА")
        print("="*50)
        print(f"Время генерации: {stats['generated_at']}")
        print()
        print("ПОЛЬЗОВАТЕЛИ:")
        print(f"  Всего пользователей: {stats['total_users']}")
        print(f"  Активных: {stats['active_users']}")
        print(f"  Заблокированных: {stats['blocked_users']}")
        print(f"  Новых за 7 дней: {stats['new_users_7d']}")
        print(f"  Новых сегодня: {stats['new_users_today']}")
        print()
        print("ЗАЯВКИ:")
        print(f"  Начали заполнение: {stats['started_applications']}")
        print(f"  Заполнили форму: {stats['filled_applications']}")
        print(f"  Подали заявку: {stats['submitted']}")
        print(f"  Не подали: {stats['not_submitted']}")
        print(f"  Новых заявок за 7 дней: {stats['new_applications_7d']}")
        print(f"  Новых заявок сегодня: {stats['new_applications_today']}")
        print()
        
        if stats['started_applications'] > 0:
            conversion_rate = round((stats['submitted'] / stats['started_applications']) * 100, 1)
            print(f"КОНВЕРСИЯ: {conversion_rate}% (подача заявок / начало заполнения)")
        
        print("="*50)
        
        # Сохраняем в CSV
        output_dir = Path("storage/analytics")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_dir / f"quick_stats_{timestamp}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = stats.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(stats)
        
        print(f"\nСтатистика сохранена в: {filepath}")
        
        return stats
        
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(get_quick_stats())