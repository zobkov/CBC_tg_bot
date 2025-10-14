#!/usr/bin/env python3
"""
Скрипт для рассылки сообщений пользователям, которые есть в evaluated_applications 
и у которых есть хотя бы одно true в accepted_1, accepted_2 или accepted_3
"""
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.services.broadcast_scheduler import send_broadcast_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='#%(levelname)-8s [%(asctime)s] - %(filename)s:%(lineno)d - %(name)s:%(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_message_to_accepted_users(message_text: str, dry_run: bool = False):
    """
    Отправляет сообщение всем пользователям, принятым хотя бы по одному заданию
    
    Args:
        message_text: Текст сообщения для отправки
        dry_run: Если True, только показывает количество пользователей без отправки
    """
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        # Создаем бот
        bot = Bot(token=config.tg_bot.token)
        
        # Подключаемся к БД заявок
        pool = await get_pg_pool(
            db_name=config.db_applications.database,
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password
        )
        
        async with pool.connection() as conn:
            # Получаем список принятых пользователей
            cursor = await conn.execute("""
                SELECT DISTINCT u.user_id, a.telegram_username, a.full_name
                FROM users u
                INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
                LEFT JOIN applications a ON u.user_id = a.user_id
                WHERE u.is_blocked = FALSE 
                AND (ea.accepted_1 = TRUE OR ea.accepted_2 = TRUE OR ea.accepted_3 = TRUE)
                ORDER BY u.user_id
            """)
            
            users = await cursor.fetchall()
            logger.info(f"Найдено {len(users)} принятых пользователей")
            
            if not users:
                logger.info("Принятые пользователи не найдены")
                return
            
            # Показываем информацию о пользователях
            print(f"\n=== Найдено {len(users)} принятых пользователей ===")
            for user in users[:10]:  # Показываем первых 10 для примера
                user_id, telegram_username, full_name = user
                print(f"ID: {user_id}, Username: @{telegram_username or 'None'}, Name: {full_name or 'None'}")
            
            if len(users) > 10:
                print(f"... и еще {len(users) - 10} пользователей")
            
            if dry_run:
                print(f"\nDRY RUN: Сообщение НЕ отправлено. Всего пользователей: {len(users)}")
                print(f"Текст сообщения:\n{message_text}")
                return
            
            # Подтверждение отправки
            print(f"\nГотов отправить сообщение {len(users)} пользователям.")
            print(f"Текст сообщения:\n{message_text}")
            confirm = input("\nПродолжить отправку? (y/N): ").strip().lower()
            
            if confirm != 'y':
                print("Отправка отменена")
                return
            
            # Отправляем рассылку через существующую функцию
            await send_broadcast_message(
                bot=bot,
                db_pool=pool,
                text=message_text,
                groups=["accepted"]
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке рассылки: {e}")
        raise
    finally:
        try:
            await bot.session.close()
        except:
            pass


async def get_accepted_users_details():
    """
    Показывает подробную информацию о принятых пользователях с разбивкой по заданиям
    """
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
            # Получаем статистику по принятым пользователям
            cursor = await conn.execute("""
                SELECT 
                    COUNT(*) as total_evaluated,
                    SUM(CASE WHEN accepted_1 = TRUE THEN 1 ELSE 0 END) as accepted_task_1,
                    SUM(CASE WHEN accepted_2 = TRUE THEN 1 ELSE 0 END) as accepted_task_2,
                    SUM(CASE WHEN accepted_3 = TRUE THEN 1 ELSE 0 END) as accepted_task_3,
                    SUM(CASE WHEN (accepted_1 = TRUE OR accepted_2 = TRUE OR accepted_3 = TRUE) THEN 1 ELSE 0 END) as accepted_any
                FROM evaluated_applications ea
                INNER JOIN users u ON ea.user_id = u.user_id
                WHERE u.is_blocked = FALSE
            """)
            
            stats = await cursor.fetchone()
            
            if stats:
                total_evaluated, accepted_1, accepted_2, accepted_3, accepted_any = stats
                print(f"\n=== Статистика принятых пользователей ===")
                print(f"Всего оцененных пользователей: {total_evaluated}")
                print(f"Принято по заданию 1: {accepted_1}")
                print(f"Принято по заданию 2: {accepted_2}")
                print(f"Принято по заданию 3: {accepted_3}")
                print(f"Принято хотя бы по одному заданию: {accepted_any}")
            
            # Получаем подробный список принятых пользователей
            cursor = await conn.execute("""
                SELECT 
                    u.user_id, a.telegram_username, a.full_name,
                    ea.accepted_1, ea.accepted_2, ea.accepted_3,
                    ea.created, ea.updated
                FROM users u
                INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
                LEFT JOIN applications a ON u.user_id = a.user_id
                WHERE u.is_blocked = FALSE 
                AND (ea.accepted_1 = TRUE OR ea.accepted_2 = TRUE OR ea.accepted_3 = TRUE)
                ORDER BY ea.updated DESC
            """)
            
            users = await cursor.fetchall()
            
            print(f"\n=== Список принятых пользователей ({len(users)}) ===")
            for user in users:
                user_id, telegram_username, full_name, acc1, acc2, acc3, created, updated = user
                tasks = []
                if acc1:
                    tasks.append("1")
                if acc2:
                    tasks.append("2")
                if acc3:
                    tasks.append("3")
                
                print(f"ID: {user_id:>8} | @{telegram_username or 'None':<15} | {full_name or 'None':<20} | Задания: {','.join(tasks)}")
                
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователях: {e}")
        raise


def load_message_from_file(file_path: str) -> str:
    """Загружает текст сообщения из файла"""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        return path.read_text(encoding='utf-8').strip()
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Скрипт для рассылки сообщений принятым пользователям"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда для отправки сообщения
    send_parser = subparsers.add_parser('send', help='Отправить сообщение')
    send_parser.add_argument(
        '--message', 
        type=str, 
        help='Текст сообщения для отправки'
    )
    send_parser.add_argument(
        '--file', 
        type=str, 
        help='Путь к файлу с текстом сообщения'
    )
    send_parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Показать количество пользователей без отправки'
    )
    
    # Команда для показа статистики
    stats_parser = subparsers.add_parser('stats', help='Показать статистику принятых пользователей')
    
    args = parser.parse_args()
    
    if args.command == 'send':
        # Определяем текст сообщения
        message_text = None
        
        if args.file:
            message_text = load_message_from_file(args.file)
        elif args.message:
            message_text = args.message
        else:
            print("Ошибка: необходимо указать текст сообщения через --message или --file")
            return
        
        if not message_text.strip():
            print("Ошибка: текст сообщения не может быть пустым")
            return
        
        # Отправляем сообщение
        asyncio.run(send_message_to_accepted_users(
            message_text=message_text,
            dry_run=args.dry_run
        ))
        
    elif args.command == 'stats':
        # Показываем статистику
        asyncio.run(get_accepted_users_details())
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()