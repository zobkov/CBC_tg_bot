"""
Утилита для обновления маппинга позиций из CSV файла
"""
import logging
from generate_position_file_mapping import generate_position_file_mapping

logger = logging.getLogger(__name__)


def update_position_file_mapping() -> bool:
    """
    Обновляет position-file_map.json из CSV файла
    
    Returns:
        bool: True если успешно, False в случае ошибки
    """
    try:
        logger.info("🔄 Обновляем маппинг файлов заданий из CSV...")
        success = generate_position_file_mapping()
        
        if success:
            # Очищаем кэш после обновления файла
            from app.utils.position_mapping import clear_mapping_cache
            clear_mapping_cache()
            logger.info("✅ Маппинг файлов заданий успешно обновлен")
        else:
            logger.error("❌ Ошибка при обновлении маппинга файлов заданий")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении маппинга: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_position_file_mapping()