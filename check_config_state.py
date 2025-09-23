#!/usr/bin/env python3
"""
Скрипт для проверки состояния конфигурационных файлов и маппингов.
Используйте для диагностики проблем на продакшене.
"""

import os
import sys
import json
import hashlib
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_file_hash(filepath):
    """Получает MD5 хэш файла"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def get_file_info(filepath):
    """Получает информацию о файле"""
    try:
        stat = os.stat(filepath)
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": get_file_hash(filepath)
        }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }

def check_config_files():
    """Проверяет состояние конфигурационных файлов"""
    print("📁 Проверка конфигурационных файлов:")
    
    config_files = [
        "config/task_file_ids.json",
        "config/position-file_map.json", 
        "config/position_id_mapping.json",
        "config/departments.json",
        "config/selection_config.json"
    ]
    
    for config_file in config_files:
        info = get_file_info(config_file)
        if info["exists"]:
            print(f"  ✅ {config_file}")
            print(f"     Размер: {info['size']} байт")
            print(f"     Изменен: {info['modified']}")
            print(f"     MD5: {info['hash']}")
        else:
            print(f"  ❌ {config_file}: {info['error']}")

def check_mappings():
    """Проверяет загрузку маппингов"""
    print("\n🗂️  Проверка загрузки маппингов:")
    
    try:
        from app.utils.task_file_id import load_task_file_ids
        task_file_ids = load_task_file_ids()
        print(f"  ✅ task_file_ids.json: {len(task_file_ids)} записей")
    except Exception as e:
        print(f"  ❌ task_file_ids.json: {e}")
    
    try:
        from app.utils.position_mapping import load_position_id_mapping
        position_mapping = load_position_id_mapping()
        print(f"  ✅ position_id_mapping.json: загружен")
        print(f"     Отделы: {len(position_mapping.get('departments_map', {}))}")
        print(f"     Подотделы: {len(position_mapping.get('subdepartments_map', {}))}")
        print(f"     Позиции: {len(position_mapping.get('positions_map', {}))}")
    except Exception as e:
        print(f"  ❌ position_id_mapping.json: {e}")
    
    try:
        from app.utils.position_mapping import load_position_file_mapping
        file_mapping = load_position_file_mapping()
        print(f"  ✅ position-file_map.json: {len(file_mapping)} записей")
    except Exception as e:
        print(f"  ❌ position-file_map.json: {e}")

def test_problematic_position():
    """Тестирует проблемную позицию из лога"""
    print("\n🔍 Тестирование проблемной позиции:")
    
    try:
        from app.utils.position_mapping import get_position_id, get_task_file_for_position
        from app.utils.task_file_id import get_task_file_id
        
        # Проблемная позиция из лога
        dept = "Отдел партнёров"
        subdept = None
        pos = "Менеджер по работе с партнерами"
        
        print(f"  Позиция: {dept} / {subdept} / {pos}")
        
        # Получаем position_id
        position_id = get_position_id(dept, subdept, pos)
        print(f"  Position ID: {position_id}")
        
        # Получаем файл задания
        task_file = get_task_file_for_position(dept, subdept, pos)
        print(f"  Task file: {task_file}")
        
        # Получаем file_id
        if task_file:
            file_id = get_task_file_id(task_file)
            print(f"  File ID: {file_id}")
            
            if file_id:
                print("  ✅ Все этапы прошли успешно")
            else:
                print("  ❌ file_id не найден")
        else:
            print("  ❌ Файл задания не найден")
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

def main():
    """Основная функция"""
    print("🔍 Диагностика состояния CBC Crew Selection Bot")
    print(f"📅 Время проверки: {datetime.now().isoformat()}")
    print(f"📂 Рабочая директория: {os.getcwd()}")
    print()
    
    check_config_files()
    check_mappings()
    test_problematic_position()
    
    print("\n✅ Диагностика завершена")

if __name__ == "__main__":
    main()