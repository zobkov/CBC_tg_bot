#!/usr/bin/env python3
"""
Скрипт для рассылки сообщений всем активным пользователям бота
"""
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='#%(levelname)-8s [%(asctime)s] - %(filename)s:%(lineno)d - %(name)s:%(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_message_to_all_users(message_text: str, dry_run: bool = False):
    """
    Отправляет сообщение всем активным пользователям бота
    
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
            # Получаем список всех активных пользователей
            cursor = await conn.execute("""
                SELECT DISTINCT u.user_id, a.telegram_username, a.full_name, u.submission_status
                FROM users u
                LEFT JOIN applications a ON u.user_id = a.user_id
                WHERE u.is_blocked = FALSE AND u.is_alive = TRUE
                ORDER BY u.user_id
            """)
            
            users = await cursor.fetchall()
            logger.info(f"Найдено {len(users)} активных пользователей")
            
            if not users:
                logger.info("Активные пользователи не найдены")
                return
            
            # Группируем пользователей по статусу
            stats = {}
            for user in users:
                user_id, telegram_username, full_name, submission_status = user
                if submission_status not in stats:
                    stats[submission_status] = 0
                stats[submission_status] += 1
            
            # Показываем информацию о пользователях
            print(f"\n=== Найдено {len(users)} активных пользователей ===")
            print("Статистика по статусам:")
            for status, count in stats.items():
                print(f"  {status}: {count}")
            
            print(f"\nПримеры пользователей (первые 10):")
            for user in users[:10]:
                user_id, telegram_username, full_name, submission_status = user
                print(f"ID: {user_id}, Username: @{telegram_username or 'None'}, Name: {full_name or 'None'}, Status: {submission_status}")
            
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
            
            # Отправляем сообщения
            sent_count = 0
            failed_count = 0
            blocked_count = 0
            
            print(f"\nНачинаем рассылку...")
            
            for i, user in enumerate(users, 1):
                user_id, telegram_username, full_name, submission_status = user
                
                try:
                    await bot.send_message(
                        chat_id=user_id, 
                        text=message_text, 
                        parse_mode='HTML'
                    )
                    sent_count += 1
                    
                    # Показываем прогресс каждые 50 сообщений
                    if i % 50 == 0:
                        print(f"Отправлено {i}/{len(users)} сообщений...")
                    
                    # Rate limiting - ограничение скорости отправки
                    await asyncio.sleep(0.05)  # 20 сообщений в секунду
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    
                    # Проверяем, заблокирован ли бот пользователем
                    if "Forbidden" in error_msg or "bot was blocked" in error_msg:
                        blocked_count += 1
                        logger.warning(f"Пользователь {user_id} заблокировал бота")
                        
                        # Обновляем статус пользователя в БД
                        try:
                            await conn.execute(
                                "UPDATE users SET is_alive = FALSE WHERE user_id = %s",
                                (user_id,)
                            )
                        except Exception:
                            pass
                    else:
                        logger.warning(f"Ошибка отправки пользователю {user_id}: {error_msg}")
            
            # Итоговая статистика
            print(f"\n=== Результаты рассылки ===")
            print(f"Всего пользователей: {len(users)}")
            print(f"Успешно отправлено: {sent_count}")
            print(f"Заблокировали бота: {blocked_count}")
            print(f"Другие ошибки: {failed_count - blocked_count}")
            print(f"Процент успешности: {(sent_count / len(users) * 100):.1f}%")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке рассылки: {e}")
        raise
    finally:
        try:
            await bot.session.close()
        except:
            pass


async def get_all_users_stats():
    """
    Показывает подробную статистику всех пользователей бота
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
            # Получаем общую статистику пользователей
            cursor = await conn.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(CASE WHEN is_alive = TRUE THEN 1 ELSE 0 END) as alive_users,
                    SUM(CASE WHEN is_blocked = FALSE THEN 1 ELSE 0 END) as not_blocked_users,
                    SUM(CASE WHEN is_alive = TRUE AND is_blocked = FALSE THEN 1 ELSE 0 END) as active_users
                FROM users
            """)
            
            stats = await cursor.fetchone()
            total_users, alive_users, not_blocked_users, active_users = stats
            
            print(f"\n=== Общая статистика пользователей ===")
            print(f"Всего пользователей в БД: {total_users}")
            print(f"Активные (is_alive=TRUE): {alive_users}")
            print(f"Не заблокированные (is_blocked=FALSE): {not_blocked_users}")
            print(f"Активные и не заблокированные: {active_users}")
            
            # Статистика по статусам заявок
            cursor = await conn.execute("""
                SELECT 
                    u.submission_status,
                    COUNT(*) as count
                FROM users u
                WHERE u.is_alive = TRUE AND u.is_blocked = FALSE
                GROUP BY u.submission_status
                ORDER BY u.submission_status
            """)
            
            submission_stats = await cursor.fetchall()
            
            print(f"\n=== Статистика по статусам заявок (активные пользователи) ===")
            for status, count in submission_stats:
                print(f"{status}: {count}")
            
            # Статистика пользователей с заявками
            cursor = await conn.execute("""
                SELECT 
                    COUNT(DISTINCT u.user_id) as users_with_applications,
                    COUNT(DISTINCT ea.user_id) as users_evaluated
                FROM users u
                LEFT JOIN applications a ON u.user_id = a.user_id
                LEFT JOIN evaluated_applications ea ON u.user_id = ea.user_id
                WHERE u.is_alive = TRUE AND u.is_blocked = FALSE
                AND a.user_id IS NOT NULL
            """)
            
            app_stats = await cursor.fetchone()
            users_with_apps, users_evaluated = app_stats
            
            print(f"\n=== Статистика заявок ===")
            print(f"Пользователи с заявками: {users_with_apps}")
            print(f"Пользователи с оценками: {users_evaluated or 0}")
                
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
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
        description="Скрипт для рассылки сообщений всем активным пользователям бота"
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
    stats_parser = subparsers.add_parser('stats', help='Показать статистику всех пользователей')
    
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
        asyncio.run(send_message_to_all_users(
            message_text=message_text,
            dry_run=args.dry_run
        ))
        
    elif args.command == 'stats':
        # Показываем статистику
        asyncio.run(get_all_users_stats())
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()