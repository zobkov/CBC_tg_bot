"""
ICS File ID Manager
Manages ICS file generation and Telegram file_id synchronization for online lectures
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional

from aiogram import Bot
from aiogram.types import FSInputFile

from app.services.ics_generator import generate_ics_file
from app.infrastructure.database.models.online_events import OnlineEventModel
from app.infrastructure.database.database.db import DB


logger = logging.getLogger(__name__)


class IcsFileIdManager:
    """Менеджер для работы с file_id файлов ICS календаря"""
    
    def __init__(
        self,
        bot: Bot,
        ics_dir: str,
        file_id_storage_path: str,
        lectures_config_path: str,
        target_chat_id: int
    ):
        self.bot = bot
        self.ics_dir = Path(ics_dir)
        self.file_id_storage_path = Path(file_id_storage_path)
        self.lectures_config_path = Path(lectures_config_path)
        self.target_chat_id = target_chat_id
        
    def _get_all_ics_files(self) -> Set[str]:
        """Получить все .ics файлы из папки (возвращает slugs без расширения)"""
        ics_files = set()
        
        for file_path in self.ics_dir.glob('*.ics'):
            if file_path.is_file():
                # Используем имя файла без расширения (slug) как ключ
                slug = file_path.stem
                ics_files.add(slug)
                
        return ics_files
    
    def _load_existing_file_ids(self) -> Dict[str, str]:
        """Загрузить существующие file_id из JSON файла"""
        if self.file_id_storage_path.exists():
            try:
                with open(self.file_id_storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Не удалось загрузить file_id из {self.file_id_storage_path}: {e}")
        return {}
    
    def _save_file_ids(self, file_ids: Dict[str, str]) -> None:
        """Сохранить file_id в JSON файл"""
        # Создаем директорию если её нет
        self.file_id_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.file_id_storage_path, 'w', encoding='utf-8') as f:
            json.dump(file_ids, f, ensure_ascii=False, indent=2)
        logger.info(f"Сохранено {len(file_ids)} ICS file_id в {self.file_id_storage_path}")
    
    async def _send_document_and_get_file_id(self, ics_path: Path, event_title: str) -> Optional[str]:
        """Отправить ICS файл и получить file_id"""
        try:
            document = FSInputFile(ics_path)
            message = await self.bot.send_document(
                chat_id=self.target_chat_id,
                document=document,
                caption=f"📅 Календарь: {event_title}"
            )
            
            if message.document:
                file_id = message.document.file_id
                logger.info(f"✅ Отправлен {ics_path.name}, file_id: {file_id}")
                return file_id
            else:
                logger.error(f"❌ Не удалось получить file_id для {ics_path.name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке {ics_path.name}: {e}")
            return None
    
    async def check_and_generate_ics_files(self, db: DB) -> int:
        """
        Проверить наличие ICS файлов и сгенерировать недостающие
        на основе данных из БД
        
        Args:
            db: Database access object
            
        Returns:
            Количество созданных файлов
        """
        logger.info("🔍 Проверка наличия ICS файлов...")
        
        # Получаем все активные события из БД
        events = await db.online_events.get_all_active()
        
        if not events:
            logger.info("ℹ️ Активных событий не найдено в БД")
            return 0
        
        # Получаем существующие ICS файлы
        existing_ics_files = self._get_all_ics_files()
        
        # Определяем, какие файлы нужно создать
        created_count = 0
        
        for event in events:
            if event.slug not in existing_ics_files:
                logger.info(f"🆕 Генерация ICS для события '{event.slug}'")
                
                try:
                    output_path = self.ics_dir / f"{event.slug}.ics"
                    generate_ics_file(event, output_path)
                    created_count += 1
                except Exception as e:
                    logger.error(f"❌ Ошибка при генерации ICS для '{event.slug}': {e}")
        
        if created_count > 0:
            logger.info(f"✅ Создано {created_count} новых ICS файлов")
        else:
            logger.info("✅ Все ICS файлы актуальны")
        
        return created_count
    
    async def check_and_upload_new_ics(self, db: DB) -> Dict[str, str]:
        """
        Проверить наличие новых ICS файлов и загрузить их file_id.
        Также генерирует недостающие ICS файлы на основе БД.
        
        Args:
            db: Database access object
            
        Returns:
            Обновленный словарь file_id
        """
        logger.info("🔍 Проверка и синхронизация ICS file_id...")
        
        # Сначала генерируем недостающие ICS файлы
        await self.check_and_generate_ics_files(db)
        
        # Получаем все ICS файлы
        all_ics_files = self._get_all_ics_files()
        
        # Загружаем существующие file_id
        existing_file_ids = self._load_existing_file_ids()
        
        # Находим новые файлы (для которых нет file_id)
        existing_slugs = set(existing_file_ids.keys())
        new_slugs = all_ics_files - existing_slugs
        
        if not new_slugs:
            logger.info("✅ Новых ICS файлов не найдено")
            return existing_file_ids
        
        logger.info(f"🆕 Найдено {len(new_slugs)} новых ICS файлов для загрузки")
        
        # Получаем события из БД для названий
        events = await db.online_events.get_all_active()
        event_map = {event.slug: event for event in events}
        
        # Отправляем новые файлы и получаем file_id
        updated_file_ids = existing_file_ids.copy()
        
        for slug in new_slugs:
            ics_path = self.ics_dir / f"{slug}.ics"
            
            if not ics_path.exists():
                logger.warning(f"ICS файл для {slug} не найден по пути {ics_path}")
                continue
            
            # Получаем название события для caption
            event = event_map.get(slug)
            event_title = event.title if event else slug
                
            file_id = await self._send_document_and_get_file_id(ics_path, event_title)
            
            if file_id:
                updated_file_ids[slug] = file_id
                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)
        
        # Сохраняем обновленные file_id
        self._save_file_ids(updated_file_ids)
        
        logger.info(f"✅ Обработано {len(new_slugs)} новых ICS файлов")
        return updated_file_ids
    
    def get_file_id(self, slug: str) -> Optional[str]:
        """Получить file_id для конкретного ICS файла по slug события"""
        file_ids = self._load_existing_file_ids()
        return file_ids.get(slug)
    
    def get_all_file_ids(self) -> Dict[str, str]:
        """Получить все file_id"""
        return self._load_existing_file_ids()


async def startup_ics_check(
    bot: Bot,
    db: DB,
    ics_dir: str = "app/bot/assets/ics",
    target_chat_id: int = 257026813,
    file_id_storage_path: str = "config/ics_file_ids.json",
    lectures_config_path: str = "config/lectures.json"
) -> Dict[str, str]:
    """
    Функция для проверки и синхронизации ICS файлов при старте бота.
    
    Args:
        bot: Экземпляр бота
        db: Database access object
        ics_dir: Путь к папке с ICS файлами
        target_chat_id: ID чата для отправки файлов (для получения file_id)
        file_id_storage_path: Путь к файлу с file_id
        lectures_config_path: Путь к конфигу лекций
        
    Returns:
        Словарь с file_id всех ICS файлов
    """
    manager = IcsFileIdManager(
        bot=bot,
        ics_dir=ics_dir,
        file_id_storage_path=file_id_storage_path,
        lectures_config_path=lectures_config_path,
        target_chat_id=target_chat_id
    )
    return await manager.check_and_upload_new_ics(db)
