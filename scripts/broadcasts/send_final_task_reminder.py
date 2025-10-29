#!/usr/bin/env python3
"""
Единоразовая рассылка по категориям для пользователей, не отправивших хотя бы одно задание, куда они были приняты.
Категории определяются по отделам/позициям заявки.
"""
import asyncio
import logging
import argparse
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool

# ID тестового пользователя
TEST_USER_ID = 257026813

# Категории и тексты
CATEGORY_TEXTS = [
    ("smm_show", "<b>Пришло время творить вместе с нами </b>⚡️\n\n你好! Сегодня заключительный день приема тестовых заданий. Мечтаешь работать в команде профессионалов и рассказывать вдохновляющую визуальную историю? Мы (и поддержка крупного банка России 👀) поможем сделать так, чтобы твоим творчеством восхищалась ребята из 80+ регионов России!\n\nНе откладывай и загружай решение сегодня до <u><b>23:59</b></u> ⏰\n\nМы с нетерпением ждём твою работу!"),
    ("smm_chinese", "<b>Последний шанс отправить тестовое задание</b> ⚡️\n\n你好! Сегодня заключительный день приема тестовых заданий. Используй этот момент по максимуму и покажи, как ты умеешь справляться с нестандартными задачами. \n\nМы не просто собираем команду – мы создаем среду, где ценят глубокое понимание культуры Поднебесной. Давай вместе создадим такой проект о Китае, который прогремит на всю Россию?\n\n抓紧啦！今晚<b>23:59</b>截止提交！⏰\n\n千里之行始于足下!"),
    ("creative", "<b>Пришло время творить вместе с нами </b>⚡️\n\n你好! Сегодня заключительный день приема тестовых заданий. Это задание не просто этап отбора, это твой шанс показать свой уникальный голос. Докажи, что твои идеи могут удивлять и вдохновлять. А мы поможем сделать так, чтобы твоим творчеством восхищалась ребята из 80+ регионов России!\n\nНе откладывай и загружай решение сегодня до <u><b>23:59</b></u> ⏰\n\nМы с нетерпением ждём твою работу!"),
    ("general", "<b>Последний шанс отправить тестовое задание</b> ⚡️\n\n你好! Сегодня заключительный день приема тестовых заданий. Используй этот момент по максимуму и покажи, как ты умеешь справляться с нестандартными задачами. \n\nНе откладывай и загружай решение сегодня до <u><b>23:59</b></u> ⏰\n\n<i>Мы с нетерпением ждём твою работу!</i>")
]

# Приоритет категорий (отдел/подотдел)
# В базе данных хранятся текстовые названия, а не ID
SMM_SHOW_DEPTS = {"Медиа-шоу"}  # SMM&PR, медиа-шоу (подотдел)
SMM_CHINESE_POSITIONS = {"Контент-менеджер со знанием китайского языка"}  # SMM&PR, контент-менеджер с китайским (позиция)
CREATIVE_DEPTS = {"Отдел дизайна", "Творческий отдел"}  # Дизайн и творческий отдел


def get_category(dept_pos_list):
    """
    dept_pos_list: list of (department, subdepartment, position) for all приоритетов пользователя
    Возвращает ключ категории по приоритету
    """
    # Проверяем медиа-шоу (приоритет 1) - по подотделу
    for dept, subdept, pos in dept_pos_list:
        if subdept in SMM_SHOW_DEPTS:
            return "smm_show"
    
    # Проверяем контент-менеджер с китайским (приоритет 2) - по позиции
    for dept, subdept, pos in dept_pos_list:
        if pos in SMM_CHINESE_POSITIONS:
            return "smm_chinese"
    
    # Проверяем творческие отделы (приоритет 3) - по отделу
    for dept, subdept, pos in dept_pos_list:
        if dept in CREATIVE_DEPTS:
            return "creative"
    
    return "general"


async def get_user_category_and_message(pool, user_id):
    """
    Получает категорию и сообщение для конкретного пользователя
    Возвращает (category_name, message_text) или None если пользователь не подходит под критерии
    """
    async with pool.connection() as conn:
        cursor = await conn.execute("""
            SELECT u.user_id,
                   ea.accepted_1, ea.accepted_2, ea.accepted_3,
                   u.task_1_submitted, u.task_2_submitted, u.task_3_submitted,
                   a.department_1, a.subdepartment_1, a.position_1,
                   a.department_2, a.subdepartment_2, a.position_2,
                   a.department_3, a.subdepartment_3, a.position_3
            FROM users u
            INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
            LEFT JOIN applications a ON u.user_id = a.user_id
            WHERE u.user_id = %s AND u.is_blocked = FALSE
        """, (user_id,))
        
        row = await cursor.fetchone()
        if not row:
            return None
            
        accepted = row[1:4]
        submitted = row[4:7]
        
        # Проверяем, есть ли хотя бы одно задание, куда принят, но не отправил
        has_unsubmitted = any(acc and not sub for acc, sub in zip(accepted, submitted))
        if not has_unsubmitted:
            return None
            
        # Собираем все приоритеты пользователя
        dept_pos = [
            (row[7], row[8], row[9]),
            (row[10], row[11], row[12]),
            (row[13], row[14], row[15])
        ]
        
        # Определяем категорию
        cat = get_category(dept_pos)
        
        # Находим текст сообщения
        for key, text in CATEGORY_TEXTS:
            if cat == key:
                return (cat, text, dept_pos)  # Добавляем dept_pos для отладки
        
        return None


async def test_single_user(user_id=TEST_USER_ID, dry_run=True):
    """
    Тестовая отправка одному пользователю
    """
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    pool = await get_pg_pool(
        db_name=config.db_applications.database,
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password
    )
    
    try:
        result = await get_user_category_and_message(pool, user_id)
        
        if result is None:
            print(f"❌ Пользователь {user_id} не подходит под критерии рассылки")
            print("Возможные причины:")
            print("- Пользователь заблокирован или не найден")
            print("- Нет записи в evaluated_applications")
            print("- Отправил все задания, куда был принят")
            return
        
        category, message, dept_pos = result
        print(f"✅ Пользователь {user_id} подходит под критерии")
        print(f"📂 Категория: {category}")
        print(f"🎯 Приоритеты пользователя:")
        for i, (dept, subdept, pos) in enumerate(dept_pos, 1):
            print(f"  {i}. Отдел: {dept}, Подотдел: {subdept}, Позиция: {pos}")
        print(f"📝 Сообщение:")
        print("-" * 50)
        print(message)
        print("-" * 50)
        
        if dry_run:
            print("\n🔍 DRY RUN: Сообщение НЕ отправлено")
            return
            
        # Подтверждение отправки
        confirm = input(f"\nОтправить сообщение пользователю {user_id}? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Отправка отменена")
            return
            
        try:
            await bot.send_message(chat_id=user_id, text=message)
            print(f"✅ Сообщение успешно отправлено пользователю {user_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
            
    except Exception as e:
        logging.error(f"Ошибка при тестировании пользователя {user_id}: {e}")
        raise
    finally:
        await bot.session.close()


async def main():
    """
    Основная функция для массовой рассылки
    """
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    pool = await get_pg_pool(
        db_name=config.db_applications.database,
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password
    )
    async with pool.connection() as conn:
        # Получаем пользователей, у которых есть хотя бы одно задание, куда они были приняты, но не отправили
        cursor = await conn.execute("""
            SELECT u.user_id,
                   ea.accepted_1, ea.accepted_2, ea.accepted_3,
                   u.task_1_submitted, u.task_2_submitted, u.task_3_submitted,
                   a.department_1, a.subdepartment_1, a.position_1,
                   a.department_2, a.subdepartment_2, a.position_2,
                   a.department_3, a.subdepartment_3, a.position_3
            FROM users u
            INNER JOIN evaluated_applications ea ON u.user_id = ea.user_id
            LEFT JOIN applications a ON u.user_id = a.user_id
            WHERE u.is_blocked = FALSE
        """)
        rows = await cursor.fetchall()
    
    # user_id -> (категория, текст)
    user_msgs = {}
    for row in rows:
        user_id = row[0]
        accepted = row[1:4]
        submitted = row[4:7]
        # Собираем все приоритеты пользователя
        dept_pos = [
            (row[7], row[8], row[9]),
            (row[10], row[11], row[12]),
            (row[13], row[14], row[15])
        ]
        # Определяем, есть ли хотя бы одно задание, куда принят, но не отправил
        has_unsubmitted = any(acc and not sub for acc, sub in zip(accepted, submitted))
        if not has_unsubmitted:
            continue
        # Определяем категорию
        cat = get_category(dept_pos)
        for key, text in CATEGORY_TEXTS:
            if cat == key:
                user_msgs[user_id] = text
                break
    print(f"Будет отправлено {len(user_msgs)} сообщений")
    # Показываем примеры
    for i, (uid, msg) in enumerate(list(user_msgs.items())[:5]):
        print(f"\n--- Пользователь {uid} ---\n{msg[:200]}...")
    # Подтверждение
    ans = input("\nОтправить рассылку? (y/N): ").strip().lower()
    if ans != 'y':
        print("Отправка отменена")
        return
    # Отправляем
    sent, errors = 0, 0
    for uid, msg in user_msgs.items():
        try:
            await bot.send_message(chat_id=uid, text=msg)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.warning(f"Ошибка отправки {uid}: {e}")
            errors += 1
    print(f"Готово! Отправлено: {sent}, ошибок: {errors}")
    await bot.session.close()


def main_cli():
    """
    CLI интерфейс для выбора режима работы
    """
    parser = argparse.ArgumentParser(
        description="Скрипт финальной рассылки по категориям"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда для тестовой отправки
    test_parser = subparsers.add_parser('test', help='Тестовая отправка одному пользователю')
    test_parser.add_argument(
        '--user-id',
        type=int,
        default=TEST_USER_ID,
        help=f'ID пользователя для тестирования (по умолчанию: {TEST_USER_ID})'
    )
    test_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Показать что будет отправлено без фактической отправки'
    )
    
    # Команда для полной рассылки
    send_parser = subparsers.add_parser('send', help='Полная рассылка всем подходящим пользователям')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        asyncio.run(test_single_user(
            user_id=args.user_id,
            dry_run=args.dry_run
        ))
    elif args.command == 'send':
        asyncio.run(main())
    else:
        parser.print_help()


if __name__ == "__main__":
    main_cli()
