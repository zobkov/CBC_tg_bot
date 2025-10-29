#!/usr/bin/env python3
"""
Скрипт для загрузки обратной связи по интервью в базу данных из CSV файла
"""

import asyncio
import csv
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import psycopg_pool
from config.config import load_config
from app.enums.roles import Role


async def load_interview_feedback_from_csv(csv_file_path: str, dry_run: bool = True):
    """
    Загружает обратную связь по интервью из CSV файла в базу данных
    
    Args:
        csv_file_path: Путь к CSV файлу
        dry_run: Если True, показывает что будет сделано без изменения БД
    """
    
    config = load_config()
    
    # Подключение к базе данных applications
    db_config = config.db_applications
    connection_string = f"postgresql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
    
    # Читаем CSV файл
    feedbacks_to_update = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                user_id = row.get('ID', '').strip()
                feedback = row.get('Обратная связь', '').strip()
                evaluation = row.get('Оценка', '').strip()
                
                if user_id:
                    try:
                        user_id_int = int(user_id)
                        
                        # Определяем роль на основе оценки
                        is_approved = evaluation.lower() in ['да', 'yes', '1', 'true']
                        new_role = Role.STAFF if is_approved else Role.GUEST
                        
                        feedbacks_to_update.append({
                            'user_id': user_id_int,
                            'feedback': feedback if feedback else None,
                            'username': row.get('Username', '').strip(),
                            'full_name': row.get('ФИО', '').strip(),
                            'evaluation': evaluation,
                            'is_approved': is_approved,
                            'new_role': new_role
                        })
                    except ValueError:
                        print(f"❌ Неверный ID пользователя: {user_id}")
                        continue
    
    except FileNotFoundError:
        print(f"❌ Файл не найден: {csv_file_path}")
        return
    except Exception as e:
        print(f"❌ Ошибка при чтении CSV файла: {e}")
        return
    
    if not feedbacks_to_update:
        print("📄 Нет данных для обновления в CSV файле")
        return
    
    print(f"📊 Найдено {len(feedbacks_to_update)} записей для обработки:")
    print("-" * 80)
    
    for item in feedbacks_to_update:
        status_emoji = "✅" if item['is_approved'] else "❌"
        role_text = item['new_role'].value.upper()
        
        print(f"👤 ID: {item['user_id']:<12} | @{item['username']:<15} | {item['full_name']}")
        print(f"{status_emoji} Оценка: {item['evaluation']:<10} | Роль: {role_text}")
        
        if item['feedback']:
            print(f"💬 Обратная связь: {item['feedback'][:50]}{'...' if len(item['feedback']) > 50 else ''}")
        else:
            print(f"💬 Обратная связь: (отсутствует)")
        print("-" * 80)
    
    if dry_run:
        print("\n🔍 DRY RUN: Изменения в базу данных НЕ внесены")
        print("Для применения изменений запустите скрипт с параметром --apply")
        return
    
    # Подтверждение перед обновлением
    confirm = input(f"\n❓ Обновить обратную связь для {len(feedbacks_to_update)} пользователей? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Операция отменена")
        return
    
    # Обновляем базу данных
    try:
        async with psycopg_pool.AsyncConnectionPool(connection_string) as pool:
            async with pool.connection() as conn:
                async with conn.cursor() as cursor:
                    
                    updated_count = 0
                    
                    for item in feedbacks_to_update:
                        try:
                            # Обновляем поле interview_feedback и роли для пользователя
                            await cursor.execute("""
                                UPDATE users 
                                SET interview_feedback = %s,
                                    roles = %s
                                WHERE user_id = %s
                            """, (item['feedback'], f'["{item["new_role"]}"]', item['user_id']))
                            
                            if cursor.rowcount > 0:
                                updated_count += 1
                                role_text = item['new_role'].value.upper()
                                feedback_text = "с обратной связью" if item['feedback'] else "без обратной связи"
                                print(f"✅ Обновлено для пользователя {item['user_id']} (@{item['username']}) - роль: {role_text}, {feedback_text}")
                            else:
                                print(f"⚠️  Пользователь {item['user_id']} не найден в БД")
                        
                        except Exception as e:
                            print(f"❌ Ошибка при обновлении пользователя {item['user_id']}: {e}")
                    
                    # Подтверждаем транзакцию
                    await conn.commit()
                    print(f"\n✅ Успешно обновлено {updated_count} из {len(feedbacks_to_update)} записей")
    
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")


def main():
    """Основная функция"""
    
    if len(sys.argv) < 2:
        print("❌ Использование: python load_interview_feedback.py <путь_к_csv_файлу> [--apply]")
        print("   --apply: применить изменения (по умолчанию dry-run)")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    dry_run = "--apply" not in sys.argv
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Файл не существует: {csv_file_path}")
        sys.exit(1)
    
    print("🔄 Загрузка обратной связи по интервью из CSV файла")
    print(f"📁 Файл: {csv_file_path}")
    print(f"🔍 Режим: {'DRY RUN' if dry_run else 'ПРИМЕНИТЬ ИЗМЕНЕНИЯ'}")
    print("=" * 80)
    
    asyncio.run(load_interview_feedback_from_csv(csv_file_path, dry_run))


if __name__ == "__main__":
    main()