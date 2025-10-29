#!/usr/bin/env python3
"""
Скрипт для рассылки сообщений одобрения/отказа по результатам интервью
"""

import asyncio
import csv
import sys
import os
from pathlib import Path
from typing import Dict, List

# Добавляем корневую директорию в путь для импортов
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import load_config


# Маппинг отделов
DEPARTMENTS = {
    1: "Выставочный отдел",
    2: "Отдел партнёров", 
    3: "Отдел SMM&PR",
    4: "Отдел логистики и ИТ",
    5: "Творческий отдел",
    6: "Отдел дизайна",
    7: "Отдел программы"
}

# Ссылки на чаты для каждого отдела (из broadcast_texts.py)
DEPARTMENT_CHATS = {
    1: "https://t.me/+4hq650-lHiU0ZDAy",
    2: "https://t.me/+3MNzPMHDgAc0ZDY6", 
    3: "https://t.me/+wJb-z446vNc2Mjli",
    4: "https://t.me/+Ey5o6Jph99pmMGRi",
    5: "https://t.me/+Cvn-ILkZedoyOGMy",
    6: "https://t.me/+9jXEiamQUP42ZGJi",
    7: "https://t.me/+GqvuJ_HtlZMxOWQy"
}


def create_acceptance_message(department: int, subdepartment: str, position: str) -> str:
    """Создает сообщение об одобрении"""
    
    # Формируем роль
    dept_name = DEPARTMENTS.get(department, f"Отдел {department}")
    role_parts = [dept_name]
    
    if subdepartment and subdepartment.strip():
        role_parts.append(subdepartment.strip())
    
    if position and position.strip():
        role_parts.append(position.strip())
    
    role = " – ".join(role_parts)
    
    # Получаем ссылку на чат
    chat_link = DEPARTMENT_CHATS.get(department, "https://t.me/+4hq650-lHiU0ZDAy")  # fallback
    
    return f"""Роль: {role}

你好!
Отбор был серьёзным испытанием. Мы внимательно изучили сотни решений, и твоё оказалось одним из самых сильных. Добро пожаловать в команду КБК!

Это то место, где все твои идеи находят живой отклик, а знакомства согревают своим теплом. Присоединяйся к чату команды — там уже собираются участники и руководители направлений, начинается обсуждение идей и подготовка к форуму.

🔗 {chat_link}

Общайся с будущими "друлегами" и заряжайся вдохновением :)

Да-да, КБК начинается прямо сейчас!"""


def create_acceptance_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для сообщения одобрения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏠 Перейти в личный кабинет",
            callback_data="start_staff_menu"
        )]
    ])


def create_decline_message() -> str:
    """Создает сообщение об отказе"""
    return """大家好!
Мы внимательно изучили сотни тестовых заданий. Конкуренция была действительно высокой, и на этот раз твоё решение не вошло в список финалистов. Это не поражение — это часть пути. Каждый отбор показывает, куда расти дальше, и даёт шанс увидеть себя с новой стороны!

Мы подготовили персональную обратную связь: руководители направлений отметили сильные стороны твоего решения и подсказали, что можно улучшить. Запросить её можно прямо в личном кабинете — она поможет сделать следующий шаг осознанно и уверенно.

Мы искренне верим, что впереди будет ещё много моментов, где твой потенциал проявится в полной мере.
КБК — это не разовый шанс, а большое движение. И мы будем рады видеть тебя снова!"""


def create_decline_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для сообщения отказа"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏠 Перейти в личный кабинет",
            callback_data="start_guest_menu"
        )]
    ])


async def parse_csv_and_prepare_messages(csv_file_path: str) -> Dict[str, List[Dict]]:
    """Парсит CSV и подготавливает сообщения для рассылки"""
    
    messages_to_send = {
        "acceptance": [],
        "decline": []
    }
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                user_id = row.get('ID', '').strip()
                username = row.get('Username', '').strip()
                full_name = row.get('ФИО', '').strip()
                department = row.get('Отдел', '').strip()
                subdepartment = row.get('Подотдел', '').strip()
                position = row.get('Вакансия', '').strip()
                evaluation = row.get('Оценка', '').strip()
                
                if not user_id:
                    continue
                
                try:
                    user_id_int = int(user_id)
                except ValueError:
                    print(f"❌ Неверный ID пользователя: {user_id}")
                    continue
                
                # Определяем тип сообщения по оценке
                if evaluation.lower() in ['да', 'yes', '1', 'true']:
                    # Одобрение
                    try:
                        dept_num = int(department) if department else 1
                        message_text = create_acceptance_message(dept_num, subdepartment, position)
                        
                        messages_to_send["acceptance"].append({
                            'user_id': user_id_int,
                            'username': username,
                            'full_name': full_name,
                            'department': dept_num,
                            'subdepartment': subdepartment,
                            'position': position,
                            'message': message_text
                        })
                    except ValueError:
                        print(f"❌ Неверный номер отдела для пользователя {user_id}: {department}")
                        continue
                        
                elif evaluation.lower() in ['нет', 'no', '0', 'false']:
                    # Отказ
                    message_text = create_decline_message()
                    
                    messages_to_send["decline"].append({
                        'user_id': user_id_int,
                        'username': username,
                        'full_name': full_name,
                        'message': message_text
                    })
                
                # Пропускаем записи с пустой оценкой
    
    except FileNotFoundError:
        print(f"❌ Файл не найден: {csv_file_path}")
        return messages_to_send
    except Exception as e:
        print(f"❌ Ошибка при чтении CSV файла: {e}")
        return messages_to_send
    
    return messages_to_send


async def send_broadcast_messages(csv_file_path: str, dry_run: bool = True):
    """Отправляет сообщения рассылки"""
    
    config = load_config()
    
    # Парсим CSV и подготавливаем сообщения
    messages = await parse_csv_and_prepare_messages(csv_file_path)
    
    total_acceptance = len(messages["acceptance"])
    total_decline = len(messages["decline"])
    total_messages = total_acceptance + total_decline
    
    if total_messages == 0:
        print("📄 Нет сообщений для отправки")
        return
    
    print(f"📊 Подготовлено сообщений:")
    print(f"   ✅ Одобрение: {total_acceptance}")
    print(f"   ❌ Отказ: {total_decline}")
    print(f"   📧 Всего: {total_messages}")
    print("=" * 80)
    
    # Показываем примеры сообщений
    if messages["acceptance"]:
        print("📝 ПРИМЕР СООБЩЕНИЯ ОДОБРЕНИЯ:")
        print("-" * 50)
        example = messages["acceptance"][0]
        print(f"👤 Пользователь: {example['full_name']} (@{example['username']}, ID: {example['user_id']})")
        print(f"📍 Роль: {DEPARTMENTS.get(example['department'], '')} – {example['subdepartment']} – {example['position']}")
        print("-" * 50)
        print(example['message'][:200] + "..." if len(example['message']) > 200 else example['message'])
        print("=" * 80)
    
    if messages["decline"]:
        print("📝 ПРИМЕР СООБЩЕНИЯ ОТКАЗА:")
        print("-" * 50)
        example = messages["decline"][0]
        print(f"👤 Пользователь: {example['full_name']} (@{example['username']}, ID: {example['user_id']})")
        print("-" * 50)
        print(example['message'][:200] + "..." if len(example['message']) > 200 else example['message'])
        print("=" * 80)
    
    if dry_run:
        print("\n🔍 DRY RUN: Сообщения НЕ отправлены")
        print("Для отправки сообщений запустите скрипт с параметром --send")
        return
    
    # Подтверждение перед отправкой
    print(f"\n❓ Отправить {total_messages} сообщений? (y/N): ", end="")
    confirm = input().strip().lower()
    
    if confirm != 'y':
        print("❌ Рассылка отменена")
        return
    
    # Инициализируем бота
    bot = Bot(token=config.tg_bot.token)
    
    sent_count = 0
    error_count = 0
    
    try:
        # Отправляем сообщения одобрения
        for msg_data in messages["acceptance"]:
            try:
                await bot.send_message(
                    chat_id=msg_data['user_id'], 
                    text=msg_data['message'],
                    reply_markup=create_acceptance_keyboard(),
                    parse_mode=None  # Отключаем парсинг разметки из-за китайских символов
                )
                sent_count += 1
                print(f"✅ Отправлено одобрение: {msg_data['full_name']} (@{msg_data['username']})")
                
                # Пауза между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                print(f"❌ Ошибка отправки {msg_data['user_id']}: {e}")
        
        # Отправляем сообщения отказа
        for msg_data in messages["decline"]:
            try:
                await bot.send_message(
                    chat_id=msg_data['user_id'], 
                    text=msg_data['message'],
                    reply_markup=create_decline_keyboard(),
                    parse_mode=None  # Отключаем парсинг разметки из-за китайских символов
                )
                sent_count += 1
                print(f"✅ Отправлен отказ: {msg_data['full_name']} (@{msg_data['username']})")
                
                # Пауза между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                print(f"❌ Ошибка отправки {msg_data['user_id']}: {e}")
    
    finally:
        await bot.session.close()
    
    print("=" * 80)
    print(f"📊 РЕЗУЛЬТАТЫ РАССЫЛКИ:")
    print(f"   ✅ Отправлено: {sent_count}")
    print(f"   ❌ Ошибок: {error_count}")
    print(f"   📧 Всего: {total_messages}")


def main():
    """Основная функция"""
    
    if len(sys.argv) < 2:
        print("❌ Использование: python send_interview_results.py <путь_к_csv_файлу> [--send]")
        print("   --send: отправить сообщения (по умолчанию dry-run)")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    dry_run = "--send" not in sys.argv
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Файл не существует: {csv_file_path}")
        sys.exit(1)
    
    print("📧 Рассылка результатов интервью")
    print(f"📁 Файл: {csv_file_path}")
    print(f"📤 Режим: {'DRY RUN' if dry_run else 'ОТПРАВКА СООБЩЕНИЙ'}")
    print("=" * 80)
    
    asyncio.run(send_broadcast_messages(csv_file_path, dry_run))


if __name__ == "__main__":
    main()