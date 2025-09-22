#!/usr/bin/env python3
"""
Скрипт для генерации position-file_map.json из CSV файла position-file_mapping.csv
"""
import csv
import json
import os
import logging

logger = logging.getLogger(__name__)


def generate_position_file_mapping():
    """Генерирует position-file_map.json из CSV файла"""
    
    csv_file_path = "position-file_mapping.csv"
    json_file_path = "config/position-file_map.json"
    
    # Проверяем существование CSV файла
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV файл не найден: {csv_file_path}")
        return False
    
    position_file_map = {}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                unique_id = row['Уникальный номер'].strip()
                task_file = row['Тестовое'].strip()
                
                if unique_id and task_file:
                    position_file_map[unique_id] = task_file
                    
        # Создаем директорию config если её нет
        os.makedirs("config", exist_ok=True)
        
        # Сохраняем JSON файл
        with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(position_file_map, jsonfile, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Создан файл {json_file_path} с {len(position_file_map)} записями")
        
        # Выводим первые несколько записей для проверки
        logger.info("Примеры записей:")
        for i, (position_id, file_name) in enumerate(position_file_map.items()):
            if i < 5:  # Показываем первые 5 записей
                logger.info(f"  {position_id} -> {file_name}")
            else:
                break
                
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при генерации position-file_map.json: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_position_file_mapping()