#!/usr/bin/env python3
"""
Скрипт для принудительной очистки всех кэшей в проекте.
Используйте при проблемах с отправкой файлов заданий на продакшене.
"""

import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_all_caches():
    """Очищает все кэши в проекте"""
    print("🧹 Очистка всех кэшей...")
    
    try:
        # Очищаем кэш file_id заданий
        from app.utils.task_file_id import clear_task_file_ids_cache
        clear_task_file_ids_cache()
        print("✅ Кэш file_id заданий очищен")
        
        # Очищаем кэш маппингов позиций
        from app.utils.position_mapping import clear_mapping_cache
        clear_mapping_cache()
        print("✅ Кэш маппингов позиций очищен")
        
        print("🎉 Все кэши успешно очищены!")
        print("💡 Рекомендуется перезапустить бот для применения изменений.")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке кэшей: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Утилита очистки кэшей CBC Crew Selection Bot")
    success = clear_all_caches()
    exit(0 if success else 1)