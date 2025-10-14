#!/usr/bin/env python3
"""
Добавляет задачу рассылки статуса заданий в broadcasts.json
"""
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Московский часовой пояс (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def add_task_status_broadcast(broadcast_file: str, datetime_str: str):
    """
    Добавляет рассылку статуса заданий в broadcasts.json
    
    Args:
        broadcast_file: Путь к файлу broadcasts.json
        datetime_str: Дата и время в формате "YYYY-MM-DDTHH:MM:SS+03:00"
    """
    
    # Шаблон для рассылки статуса заданий
    # Этот шаблон будет заменен на персонализированные сообщения в скрипте
    broadcast_template = {
        "datetime": datetime_str,
        "text": "TASK_STATUS_BROADCAST_PLACEHOLDER",
        "groups": ["accepted"]
    }
    
    # Читаем текущий файл broadcasts.json
    broadcasts_path = Path(broadcast_file)
    
    if broadcasts_path.exists():
        with open(broadcasts_path, 'r', encoding='utf-8') as f:
            broadcasts = json.load(f)
    else:
        broadcasts = []
    
    # Добавляем новую рассылку
    broadcasts.append(broadcast_template)
    
    # Сортируем по дате
    broadcasts.sort(key=lambda x: x['datetime'])
    
    # Записываем обратно в файл
    with open(broadcasts_path, 'w', encoding='utf-8') as f:
        json.dump(broadcasts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Добавлена рассылка статуса заданий на {datetime_str}")
    print(f"📝 Файл: {broadcasts_path}")
    print(f"📊 Всего рассылок в файле: {len(broadcasts)}")
    
    # Показываем что добавили
    print("\nДобавленная запись:")
    print(json.dumps(broadcast_template, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Добавляет рассылку статуса заданий в broadcasts.json"
    )
    
    parser.add_argument(
        'datetime',
        help='Дата и время в формате "YYYY-MM-DDTHH:MM:SS+03:00" (например: "2025-10-01T18:00:00+03:00")'
    )
    
    parser.add_argument(
        '--file',
        default='config/broadcasts.json',
        help='Путь к файлу broadcasts.json (по умолчанию: config/broadcasts.json)'
    )
    
    args = parser.parse_args()
    
    # Проверяем формат даты
    try:
        dt = datetime.fromisoformat(args.datetime)
        if dt.tzinfo is None:
            print("❌ Ошибка: укажите часовой пояс (например: +03:00)")
            return
    except ValueError as e:
        print(f"❌ Ошибка формата даты: {e}")
        print("Используйте формат: YYYY-MM-DDTHH:MM:SS+03:00")
        print("Пример: 2025-10-01T18:00:00+03:00")
        return
    
    add_task_status_broadcast(args.file, args.datetime)


if __name__ == "__main__":
    main()