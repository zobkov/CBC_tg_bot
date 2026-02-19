"""
ICS File ID Utilities
Provides convenient access to Telegram file_id for ICS calendar files
"""

import json
import logging
import os
from functools import lru_cache
from typing import Optional


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_ics_file_ids() -> dict:
    """
    Загрузить file_id для ICS файлов из JSON конфига.
    Использует кэширование для оптимизации производительности.
    
    Returns:
        Словарь {slug: file_id}
    """
    ics_file_ids_path = os.path.join(
        os.path.dirname(__file__),
        '../../config/ics_file_ids.json'
    )
    
    if not os.path.exists(ics_file_ids_path):
        logger.warning(f"ICS file_ids config not found at {ics_file_ids_path}")
        return {}
    
    try:
        with open(ics_file_ids_path, 'r', encoding='utf-8') as f:
            file_ids = json.load(f)
            logger.debug(f"Loaded {len(file_ids)} ICS file_id entries")
            return file_ids
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load ICS file_ids: {e}")
        return {}


def get_ics_file_id(slug: str) -> Optional[str]:
    """
    Получить file_id для ICS файла по slug события
    
    Args:
        slug: Уникальный идентификатор события (например, "lecture_1337")
    
    Returns:
        Telegram file_id или None если не найден
    """
    file_ids = load_ics_file_ids()
    file_id = file_ids.get(slug)
    
    if not file_id:
        logger.warning(f"No file_id found for ICS file with slug: {slug}")
    
    return file_id


def get_all_ics_file_ids() -> dict:
    """
    Получить все ICS file_id
    
    Returns:
        Словарь {slug: file_id}
    """
    return load_ics_file_ids()
