"""
Service for syncing online lectures from config to database
"""
import json
import logging
from pathlib import Path

from app.infrastructure.database.database.db import DB
from app.utils.datetime_formatters import parse_config_datetime

logger = logging.getLogger(__name__)


async def sync_lectures_from_config(db: DB, config_path: str = "config/lectures.json") -> int:
    """
    Синхронизирует лекции из JSON конфига в базу данных.
    
    Args:
        db: Database instance
        config_path: Путь к файлу конфигурации
    
    Returns:
        Количество синхронизированных лекций
    """
    lectures_file = Path(config_path)
    
    if not lectures_file.exists():
        logger.warning("Lectures config file not found: %s", config_path)
        return 0
    
    try:
        with open(lectures_file, "r", encoding="utf-8") as f:
            lectures_config = json.load(f)
        
        if not isinstance(lectures_config, list):
            logger.error("Lectures config must be a list")
            return 0
        
        synced_count = 0
        
        for lecture in lectures_config:
            try:
                # Валидация обязательных полей
                required_fields = ["slug", "alias", "title", "start_at", "end_at"]
                missing_fields = [field for field in required_fields if field not in lecture]
                
                if missing_fields:
                    logger.warning(
                        "Skipping lecture - missing fields: %s. Lecture: %s",
                        missing_fields,
                        lecture.get("slug", "unknown"),
                    )
                    continue
                
                # Парсим даты
                start_at = parse_config_datetime(lecture["start_at"])
                end_at = parse_config_datetime(lecture["end_at"])
                
                # Upsert в базу данных
                await db.online_events.upsert_from_config(
                    slug=lecture["slug"],
                    alias=lecture["alias"],
                    title=lecture["title"],
                    speaker=lecture.get("speaker"),
                    description=lecture.get("description"),
                    url=lecture.get("url"),
                    start_at=start_at,
                    end_at=end_at,
                )
                
                synced_count += 1
                
            except Exception as e:
                logger.error(
                    "Error syncing lecture %s: %s",
                    lecture.get("slug", "unknown"),
                    e,
                    exc_info=True,
                )
                continue
        
        # Flush изменений
        await db.session.flush()
        
        logger.info("Successfully synced %d lectures from config", synced_count)
        return synced_count
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse lectures config JSON: %s", e)
        return 0
    except Exception as e:
        logger.error("Failed to sync lectures from config: %s", e, exc_info=True)
        return 0
