"""
Утилиты для работы с маппингом позиций в уникальные ID
"""
import json
import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_position_id_mapping() -> Dict[str, Any]:
    """Загружает маппинг позиций из JSON файла (с кэшированием)"""
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), '../../config/position_id_mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
            logger.debug("Загружен маппинг position_id_mapping.json")
            return mapping
    except Exception as e:
        logger.error(f"Ошибка загрузки position_id_mapping.json: {e}")
        return {}


@lru_cache(maxsize=1)
def load_position_file_mapping() -> Dict[str, str]:
    """Загружает маппинг position_id -> файл из JSON файла (с кэшированием)"""
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), '../../config/position-file_map.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
            logger.debug("Загружен маппинг position-file_map.json")
            return mapping
    except Exception as e:
        logger.error(f"Ошибка загрузки position-file_map.json: {e}")
        return {}


def clear_mapping_cache():
    """Очищает кэш маппингов (использовать после обновления файлов)"""
    load_position_id_mapping.cache_clear()
    load_position_file_mapping.cache_clear()
    logger.info("Кэш маппингов очищен")


def get_position_id(department: str, subdepartment: Optional[str], position: str) -> Optional[str]:
    """
    Преобразует департамент, подотдел и позицию в уникальный position_id
    
    Args:
        department: Название отдела
        subdepartment: Название подотдела (может быть None)
        position: Название позиции
        
    Returns:
        str: Уникальный ID в формате "1.2.3" или None если не найден
    """
    mapping = load_position_id_mapping()
    
    if not mapping:
        logger.error("Не удалось загрузить маппинг позиций")
        return None
    
    try:
        # Получаем ID отдела
        dept_id = mapping.get('departments_map', {}).get(department)
        if dept_id is None:
            logger.warning(f"Отдел не найден в маппинге: {department}")
            return None
        
        # Получаем ID подотдела (0 если нет подотдела)
        subdept_id = 0
        if subdepartment:
            subdept_id = mapping.get('subdepartments_map', {}).get(subdepartment)
            if subdept_id is None:
                logger.warning(f"Подотдел не найден в маппинге: {subdepartment}")
                return None
        
        # Получаем ID позиции
        position_id = mapping.get('positions_map', {}).get(position)
        if position_id is None:
            logger.warning(f"Позиция не найдена в маппинге: {position}")
            return None
        
        # Формируем уникальный ID
        unique_id = f"{dept_id}.{subdept_id}.{position_id}"
        logger.debug(f"Сгенерирован position_id: {department} / {subdepartment} / {position} -> {unique_id}")
        
        return unique_id
        
    except Exception as e:
        logger.error(f"Ошибка при генерации position_id: {e}")
        return None


def get_task_file_for_position(department: str, subdepartment: Optional[str], position: str) -> Optional[str]:
    """
    Получает файл задания для указанной позиции
    
    Args:
        department: Название отдела
        subdepartment: Название подотдела (может быть None)
        position: Название позиции
        
    Returns:
        str: Название файла задания или None если не найден
    """
    # Получаем position_id
    position_id = get_position_id(department, subdepartment, position)
    if not position_id:
        return None
    
    # Получаем маппинг файлов
    file_mapping = load_position_file_mapping()
    if not file_mapping:
        logger.error("Не удалось загрузить маппинг файлов")
        return None
    
    # Возвращаем файл для position_id
    task_file = file_mapping.get(position_id)
    if task_file:
        logger.debug(f"Найден файл для position_id {position_id}: {task_file}")
    else:
        logger.warning(f"Файл не найден для position_id: {position_id}")
    
    return task_file