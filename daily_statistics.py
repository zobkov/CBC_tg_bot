#!/usr/bin/env python3
"""
Скрипт для извлечения ежедневной статистики из базы данных КБК.
Генерирует CSV файлы с различными метриками.
"""
import asyncio
import csv
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import psycopg
from typing import List, Dict, Any

from config.config import load_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatisticsGenerator:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.output_dir = Path("storage/analytics")
        self.output_dir.mkdir(exist_ok=True, parents=True)

    async def connect_db(self):
        """Подключение к базе данных заявок"""
        connection_string = (
            f"postgresql://{self.config.db_applications.user}:"
            f"{self.config.db_applications.password}@"
            f"{self.config.db_applications.host}:"
            f"{self.config.db_applications.port}/"
            f"{self.config.db_applications.database}"
        )
        self.connection = await psycopg.AsyncConnection.connect(connection_string)
        logger.info("Connected to applications database")

    async def close_db(self):
        """Закрытие соединения с БД"""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def get_daily_user_stats(self) -> List[Dict[str, Any]]:
        """
        Получает ежедневную статистику пользователей:
        - Общее количество пользователей
        - Новые пользователи за день
        - Заблокированные пользователи
        - Активные пользователи
        """
        query = """
        WITH date_range AS (
            SELECT generate_series(
                COALESCE((SELECT MIN(DATE(created)) FROM users), CURRENT_DATE - INTERVAL '30 days'),
                CURRENT_DATE,
                '1 day'::interval
            )::date AS date
        ),
        daily_stats AS (
            SELECT 
                DATE(created) as date,
                COUNT(*) as new_users,
                COUNT(*) FILTER (WHERE is_blocked = TRUE) as new_blocked_users,
                COUNT(*) FILTER (WHERE is_alive = TRUE) as new_active_users
            FROM users 
            GROUP BY DATE(created)
        )
        SELECT 
            dr.date,
            COALESCE(ds.new_users, 0) as new_users,
            COALESCE(ds.new_blocked_users, 0) as new_blocked_users, 
            COALESCE(ds.new_active_users, 0) as new_active_users,
            COALESCE(SUM(ds.new_users) OVER (ORDER BY dr.date ROWS UNBOUNDED PRECEDING), 0) as total_users,
            COALESCE(SUM(ds.new_blocked_users) OVER (ORDER BY dr.date ROWS UNBOUNDED PRECEDING), 0) as total_blocked_users,
            COALESCE(SUM(ds.new_active_users) OVER (ORDER BY dr.date ROWS UNBOUNDED PRECEDING), 0) as total_active_users
        FROM date_range dr
        LEFT JOIN daily_stats ds ON dr.date = ds.date
        ORDER BY dr.date;
        """
        
        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()
        
        stats = []
        for row in rows:
            stats.append({
                'date': row[0],
                'new_users': row[1],
                'new_blocked_users': row[2],
                'new_active_users': row[3],
                'total_users': row[4],
                'total_blocked_users': row[5],
                'total_active_users': row[6]
            })
        
        logger.info(f"Retrieved {len(stats)} days of user statistics")
        return stats

    async def get_daily_application_stats(self) -> List[Dict[str, Any]]:
        """
        Получает ежедневную статистику заявок:
        - Начатые заявки (созданные записи в applications)
        - Отправленные заявки (со статусом submitted)
        """
        query = """
        WITH date_range AS (
            SELECT generate_series(
                COALESCE((SELECT MIN(DATE(created)) FROM applications), CURRENT_DATE - INTERVAL '30 days'),
                CURRENT_DATE,
                '1 day'::interval
            )::date AS date
        ),
        daily_applications AS (
            SELECT 
                DATE(a.created) as date,
                COUNT(*) as started_applications,
                COUNT(*) FILTER (WHERE u.submission_status = 'submitted') as submitted_applications
            FROM applications a
            LEFT JOIN users u ON a.user_id = u.user_id
            GROUP BY DATE(a.created)
        )
        SELECT 
            dr.date,
            COALESCE(da.started_applications, 0) as started_applications,
            COALESCE(da.submitted_applications, 0) as submitted_applications,
            COALESCE(SUM(da.started_applications) OVER (ORDER BY dr.date ROWS UNBOUNDED PRECEDING), 0) as total_started,
            COALESCE(SUM(da.submitted_applications) OVER (ORDER BY dr.date ROWS UNBOUNDED PRECEDING), 0) as total_submitted
        FROM date_range dr
        LEFT JOIN daily_applications da ON dr.date = da.date
        ORDER BY dr.date;
        """
        
        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()
        
        stats = []
        for row in rows:
            stats.append({
                'date': row[0],
                'started_applications': row[1],
                'submitted_applications': row[2], 
                'total_started': row[3],
                'total_submitted': row[4]
            })
        
        logger.info(f"Retrieved {len(stats)} days of application statistics")
        return stats

    async def get_daily_block_stats(self) -> List[Dict[str, Any]]:
        """
        Получает ежедневную статистику блокировок бота
        Примечание: данные о блокировках могут быть неполными, 
        так как статус блокировки обновляется только при попытке отправки сообщения
        """
        query = """
        WITH date_range AS (
            SELECT generate_series(
                COALESCE((SELECT MIN(DATE(created)) FROM users), CURRENT_DATE - INTERVAL '30 days'),
                CURRENT_DATE,
                '1 day'::interval
            )::date AS date
        )
        SELECT 
            dr.date,
            COALESCE(COUNT(u.user_id) FILTER (WHERE u.is_blocked = TRUE AND DATE(u.created) = dr.date), 0) as new_blocks,
            COALESCE(COUNT(u.user_id) FILTER (WHERE u.is_blocked = TRUE), 0) as total_blocks
        FROM date_range dr
        LEFT JOIN users u ON DATE(u.created) <= dr.date
        GROUP BY dr.date
        ORDER BY dr.date;
        """
        
        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()
        
        stats = []
        for row in rows:
            stats.append({
                'date': row[0],
                'new_blocks': row[1],
                'total_blocks': row[2]
            })
        
        logger.info(f"Retrieved {len(stats)} days of block statistics")
        return stats

    async def get_submission_status_breakdown(self) -> List[Dict[str, Any]]:
        """
        Получает разбивку по статусам подачи заявок
        """
        query = """
        SELECT 
            submission_status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM users
        GROUP BY submission_status
        ORDER BY count DESC;
        """
        
        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()
        
        stats = []
        for row in rows:
            stats.append({
                'submission_status': row[0],
                'count': row[1],
                'percentage': row[2]
            })
        
        logger.info(f"Retrieved submission status breakdown for {len(stats)} statuses")
        return stats

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Сохраняет данные в CSV файл"""
        if not data:
            logger.warning(f"No data to save for {filename}")
            return
            
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        logger.info(f"Saved {len(data)} rows to {filepath}")

    async def generate_all_statistics(self):
        """Генерирует все типы статистики и сохраняет в CSV файлы"""
        try:
            await self.connect_db()
            
            # Генерируем timestamp для уникальности файлов
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Статистика пользователей
            logger.info("Generating user statistics...")
            user_stats = await self.get_daily_user_stats()
            self.save_to_csv(user_stats, f"daily_user_stats_{timestamp}.csv")
            
            # Статистика заявок
            logger.info("Generating application statistics...")
            app_stats = await self.get_daily_application_stats()
            self.save_to_csv(app_stats, f"daily_application_stats_{timestamp}.csv")
            
            # Статистика блокировок
            logger.info("Generating block statistics...")
            block_stats = await self.get_daily_block_stats()
            self.save_to_csv(block_stats, f"daily_block_stats_{timestamp}.csv")
            
            # Разбивка по статусам
            logger.info("Generating submission status breakdown...")
            status_breakdown = await self.get_submission_status_breakdown()
            self.save_to_csv(status_breakdown, f"submission_status_breakdown_{timestamp}.csv")
            
            # Создаем сводный файл
            summary_stats = {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_users': user_stats[-1]['total_users'] if user_stats else 0,
                'total_applications_started': app_stats[-1]['total_started'] if app_stats else 0,
                'total_applications_submitted': app_stats[-1]['total_submitted'] if app_stats else 0,
                'total_blocked_users': block_stats[-1]['total_blocks'] if block_stats else 0,
                'files_generated': [
                    f"daily_user_stats_{timestamp}.csv",
                    f"daily_application_stats_{timestamp}.csv", 
                    f"daily_block_stats_{timestamp}.csv",
                    f"submission_status_breakdown_{timestamp}.csv"
                ]
            }
            
            self.save_to_csv([summary_stats], f"statistics_summary_{timestamp}.csv")
            
            logger.info("All statistics generated successfully!")
            
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            raise
        finally:
            await self.close_db()


async def main():
    """Главная функция"""
    logger.info("Starting daily statistics generation...")
    
    config = load_config()
    generator = StatisticsGenerator(config)
    
    await generator.generate_all_statistics()
    
    logger.info("Statistics generation completed!")


if __name__ == "__main__":
    asyncio.run(main())