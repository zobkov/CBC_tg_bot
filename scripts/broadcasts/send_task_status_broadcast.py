#!/usr/bin/env python3
"""
Скрипт для рассылки статуса заданий пользователям категории "accepted".
Показывает статус отправки заданий по каждой из трех вакансий.
"""
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='#%(levelname)-8s [%(asctime)s] - %(filename)s:%(lineno)d - %(name)s:%(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ID тестового пользователя
TEST_USER_ID = 257026813


async def get_user_task_status(pool, user_id: int) -> Dict[str, str]:
    """
    Получает статус заданий для конкретного пользователя
    
    Returns:
        Dict с ключами 'task_1', 'task_2', 'task_3' и значениями:
        - "решение отправлено" - если принят и отправил решение
        - "решение не отправлено" - если принят но не отправил решение  
        - "–" - если не принят для этого задания
    """
    async with pool.connection() as conn:
        # Получаем данные о принятии и отправке заданий
        cursor = await conn.execute("""
            SELECT 
                u.task_1_submitted, u.task_2_submitted, u.task_3_submitted,
                ea.accepted_1, ea.accepted_2, ea.accepted_3
            FROM users u
            LEFT JOIN evaluated_applications ea ON u.user_id = ea.user_id
            WHERE u.user_id = %s
        """, (user_id,))
        
        result = await cursor.fetchone()
        
        if not result:
            # Пользователь не найден
            return {
                "task_1": "–",
                "task_2": "–", 
                "task_3": "–"
            }
        
        task_1_submitted, task_2_submitted, task_3_submitted, accepted_1, accepted_2, accepted_3 = result
        
        # Если нет записи в evaluated_applications, значит не принят
        if accepted_1 is None:
            accepted_1 = False
        if accepted_2 is None:
            accepted_2 = False
        if accepted_3 is None:
            accepted_3 = False
        
        status = {}
        
        for task_num in [1, 2, 3]:
            accepted = [accepted_1, accepted_2, accepted_3][task_num - 1]
            submitted = [task_1_submitted, task_2_submitted, task_3_submitted][task_num - 1]
            
            if not accepted:
                status[f"task_{task_num}"] = "🔒"
            elif submitted:
                status[f"task_{task_num}"] = "решение отправлено"
            else:
                status[f"task_{task_num}"] = "решение не отправлено"
        
        return status


async def get_accepted_users_with_status(pool) -> List[Tuple[int, Dict[str, str]]]:
    """
    Получает список всех принятых пользователей со статусом их заданий
    
    Returns:
        List of tuples: (user_id, task_status_dict)
    """
    async with pool.connection() as conn:
        # Получаем список принятых пользователей
        cursor = await conn.execute("""
            SELECT DISTINCT u.user_id
            FROM users u
            INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
            WHERE u.is_blocked = FALSE 
            AND (ea.accepted_1 = TRUE OR ea.accepted_2 = TRUE OR ea.accepted_3 = TRUE)
            ORDER BY u.user_id
        """)
        
        user_ids = [row[0] for row in await cursor.fetchall()]
    
    # Получаем статус заданий для каждого пользователя
    users_with_status = []
    for user_id in user_ids:
        status = await get_user_task_status(pool, user_id)
        users_with_status.append((user_id, status))
    
    return users_with_status


def format_task_status_message(task_status: Dict[str, str]) -> str:
    """
    Форматирует сообщение со статусом заданий для пользователя
    """
    message_template = """⏰ <b>Второй этап отбора КБК'26 завершится уже совсем скоро!</b>

你好! Спасибо за прохождение первого этапа отбора. Твоя заявка нас очень впечатлила. Тестовое задание — это возможность раскрыть свой потенциал и показать сильные стороны. Не упусти свой шанс создать что-то действительно крутое вместе!

<b>Твой статус:</b>
Вакансия №1: {task_1_status}
Вакансия №2: {task_2_status}
Вакансия №3: {task_3_status}

‼️ <b>Важно:</b> чтобы мы проверили задание, надо <u><b>обязательно</b></u> завершить задание.
Ответы на часто задаваемые вопросы можно найти тут: https://docs.google.com/document/d/1fV2IA_k5eY3TSM4Xue1sYR1OS8-AkHDGN_t4ubKNMlA/edit?usp=sharing

<b>Остались вопросы? Мы всегда на связи!</b>
Тех. поддержка: @zobko
Общие вопросы, связанные с отбором: @cbc_assistant"""
    
    return message_template.format(
        task_1_status=task_status["task_1"],
        task_2_status=task_status["task_2"],
        task_3_status=task_status["task_3"]
    )


async def send_task_status_broadcast(test_mode: bool = True, dry_run: bool = False):
    """
    Отправляет рассылку со статусом заданий
    
    Args:
        test_mode: Если True, отправляет только тестовому пользователю
        dry_run: Если True, только показывает что будет отправлено
    """
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        # Создаем бот
        bot = Bot(
            token=config.tg_bot.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        
        # Подключаемся к БД заявок
        pool = await get_pg_pool(
            db_name=config.db_applications.database,
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password
        )
        
        if test_mode:
            # Тестовый режим - только одному пользователю
            logger.info("Тестовый режим: отправка только пользователю %d", TEST_USER_ID)
            task_status = await get_user_task_status(pool, TEST_USER_ID)
            message_text = format_task_status_message(task_status)
            
            print(f"\n=== ТЕСТОВЫЙ РЕЖИМ ===")
            print(f"Пользователь ID: {TEST_USER_ID}")
            print(f"Статус заданий: {task_status}")
            print(f"Сообщение:")
            print(message_text)
            
            if dry_run:
                print("\nDRY RUN: Сообщение НЕ отправлено")
                return
            
            # Подтверждение отправки
            confirm = input("\nОтправить тестовое сообщение? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Отправка отменена")
                return
            
            try:
                await bot.send_message(chat_id=TEST_USER_ID, text=message_text)
                print("✅ Тестовое сообщение отправлено успешно")
            except Exception as e:
                print(f"❌ Ошибка отправки тестовому пользователю: {e}")
        
        else:
            # Полная рассылка всем принятым пользователям
            users_with_status = await get_accepted_users_with_status(pool)
            
            print(f"\n=== ПОЛНАЯ РАССЫЛКА ===")
            print(f"Найдено {len(users_with_status)} принятых пользователей")
            
            # Показываем первых 5 для примера
            print("\nПример сообщений (первые 5 пользователей):")
            for i, (user_id, task_status) in enumerate(users_with_status[:5]):
                print(f"\n--- Пользователь {user_id} ---")
                print(f"Статус: {task_status}")
                message = format_task_status_message(task_status)
                print(f"Сообщение:\n{message[:200]}...")
            
            if len(users_with_status) > 5:
                print(f"\n... и еще {len(users_with_status) - 5} пользователей")
            
            if dry_run:
                print(f"\nDRY RUN: Сообщения НЕ отправлены. Всего пользователей: {len(users_with_status)}")
                return
            
            # Подтверждение отправки
            confirm = input(f"\nОтправить персонализированные сообщения {len(users_with_status)} пользователям? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Отправка отменена")
                return
            
            # Отправляем сообщения
            sent_count = 0
            error_count = 0
            
            for user_id, task_status in users_with_status:
                try:
                    message_text = format_task_status_message(task_status)
                    await bot.send_message(chat_id=user_id, text=message_text)
                    sent_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(0.05)
                    
                    if sent_count % 50 == 0:
                        logger.info("Отправлено %d сообщений", sent_count)
                        
                except Exception as e:
                    error_count += 1
                    logger.warning("Ошибка отправки пользователю %d: %s", user_id, e)
            
            print(f"\n✅ Рассылка завершена!")
            print(f"Отправлено: {sent_count}")
            print(f"Ошибок: {error_count}")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке рассылки: {e}")
        raise
    finally:
        try:
            await bot.session.close()
        except:
            pass


async def show_task_statistics():
    """
    Показывает статистику по статусу заданий принятых пользователей
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
        
        users_with_status = await get_accepted_users_with_status(pool)
        
        print(f"\n=== Статистика по статусу заданий ===")
        print(f"Всего принятых пользователей: {len(users_with_status)}")
        
        # Подсчитываем статистику по каждому заданию
        for task_num in [1, 2, 3]:
            task_key = f"task_{task_num}"
            
            submitted_count = sum(1 for _, status in users_with_status if status[task_key] == "решение отправлено")
            not_submitted_count = sum(1 for _, status in users_with_status if status[task_key] == "решение не отправлено")
            not_accepted_count = sum(1 for _, status in users_with_status if status[task_key] == "🔒")
            
            print(f"\nЗадание {task_num}:")
            print(f"  Решение отправлено: {submitted_count}")
            print(f"  Решение не отправлено: {not_submitted_count}")
            print(f"  Не принят: {not_accepted_count}")
            print(f"  Итого принятых: {submitted_count + not_submitted_count}")
        
        # Показываем детали для тестового пользователя
        test_user_status = await get_user_task_status(pool, TEST_USER_ID)
        print(f"\n=== Тестовый пользователь {TEST_USER_ID} ===")
        print(f"Статус заданий: {test_user_status}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Скрипт для рассылки статуса заданий принятым пользователям"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда для отправки сообщений
    send_parser = subparsers.add_parser('send', help='Отправить рассылку со статусом заданий')
    send_parser.add_argument(
        '--test', 
        action='store_true', 
        help='Тестовый режим - отправка только тестовому пользователю'
    )
    send_parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Показать что будет отправлено без фактической отправки'
    )
    
    # Команда для показа статистики
    stats_parser = subparsers.add_parser('stats', help='Показать статистику по статусу заданий')
    
    args = parser.parse_args()
    
    if args.command == 'send':
        # Отправляем рассылку
        asyncio.run(send_task_status_broadcast(
            test_mode=args.test,
            dry_run=args.dry_run
        ))
        
    elif args.command == 'stats':
        # Показываем статистику
        asyncio.run(show_task_statistics())
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()