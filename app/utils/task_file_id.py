"""
Утилита для получения file_id файлов заданий
"""
import json
import os
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_task_file_ids() -> dict:
    """Загружает file_id файлов заданий из JSON файла (с кэшированием)"""
    try:
        task_file_ids_path = os.path.join(os.path.dirname(__file__), '../../config/task_file_ids.json')
        with open(task_file_ids_path, 'r', encoding='utf-8') as f:
            file_ids = json.load(f)
            logger.debug("Загружен маппинг task_file_ids.json")
            return file_ids
    except Exception as e:
        logger.error(f"Ошибка загрузки task_file_ids.json: {e}")
        return {}


def get_task_file_id(task_name: str) -> Optional[str]:
    """
    Получает file_id для файла задания по имени
    
    Args:
        task_name: Имя файла задания (без расширения)
        
    Returns:
        str: file_id или None если не найден
    """
    file_ids = load_task_file_ids()
    file_id = file_ids.get(task_name)
    
    if file_id:
        logger.debug(f"Найден file_id для задания {task_name}: {file_id}")
    else:
        logger.warning(f"file_id не найден для задания: {task_name}")
    
    return file_id


def clear_task_file_ids_cache():
    """Очищает кэш file_id заданий (использовать после обновления файлов)"""
    load_task_file_ids.cache_clear()
    logger.info("Кэш file_id заданий очищен")