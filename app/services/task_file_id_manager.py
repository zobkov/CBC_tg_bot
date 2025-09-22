import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Set, Optional

from aiogram import Bot
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)


class TaskFileIdManager:
    """Менеджер для работы с file_id файлов заданий"""
    
    def __init__(self, bot: Bot, tasks_dir: str, file_id_storage_path: str, target_chat_id: int):
        self.bot = bot
        self.tasks_dir = Path(tasks_dir)
        self.file_id_storage_path = Path(file_id_storage_path)
        self.target_chat_id = target_chat_id
        
    def _get_all_task_files(self) -> Set[str]:
        """Получить все файлы заданий из папки tasks (только имена файлов)"""
        task_extensions = {'.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
        task_files = set()
        
        for file_path in self.tasks_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in task_extensions:
                # Используем только имя файла без расширения как ключ
                task_name = file_path.stem
                task_files.add(task_name)
                
        return task_files
    
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
        logger.info(f"Сохранено {len(file_ids)} task file_id в {self.file_id_storage_path}")
    
    def _find_task_file(self, task_name: str) -> Optional[Path]:
        """Найти файл задания по имени (без расширения)"""
        task_extensions = {'.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
        
        for file_path in self.tasks_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in task_extensions:
                if file_path.stem == task_name:
                    return file_path
        return None
    
    async def _send_document_and_get_file_id(self, task_path: Path, task_name: str) -> Optional[str]:
        """Отправить файл задания и получить file_id"""
        try:
            document = FSInputFile(task_path)
            message = await self.bot.send_document(
                chat_id=self.target_chat_id,
                document=document,
                caption=f"📋 Task: {task_name}"
            )
            
            if message.document:
                file_id = message.document.file_id
                logger.info(f"✅ Отправлен {task_path.name}, file_id: {file_id}")
                return file_id
            else:
                logger.error(f"❌ Не удалось получить file_id для {task_path.name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке {task_path.name}: {e}")
            return None
    
    async def check_and_upload_new_tasks(self) -> Dict[str, str]:
        """
        Проверить наличие новых файлов заданий и загрузить их file_id.
        Возвращает обновленный словарь file_id.
        """
        logger.info("🔍 Проверка наличия новых файлов заданий...")
        
        # Получаем все файлы заданий
        all_tasks = self._get_all_task_files()
        
        # Загружаем существующие file_id
        existing_file_ids = self._load_existing_file_ids()
        
        # Находим новые файлы
        existing_tasks = set(existing_file_ids.keys())
        new_tasks = all_tasks - existing_tasks
        
        if not new_tasks:
            logger.info("✅ Новых файлов заданий не найдено")
            return existing_file_ids
        
        logger.info(f"🆕 Найдено {len(new_tasks)} новых файлов заданий")
        
        # Отправляем новые файлы и получаем file_id
        updated_file_ids = existing_file_ids.copy()
        
        for task_name in new_tasks:
            task_path = self._find_task_file(task_name)
            if not task_path:
                logger.warning(f"Файл для задания {task_name} не найден")
                continue
                
            file_id = await self._send_document_and_get_file_id(task_path, task_name)
            
            if file_id:
                updated_file_ids[task_name] = file_id
                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)
        
        # Сохраняем обновленные file_id
        self._save_file_ids(updated_file_ids)
        
        logger.info(f"✅ Обработано {len(new_tasks)} новых файлов заданий")
        return updated_file_ids
    
    async def regenerate_all_file_ids(self) -> Dict[str, str]:
        """
        Полностью пересоздать словарь file_id для всех файлов заданий.
        Используется для принудительного обновления всех file_id.
        """
        logger.info("🔄 Полная регенерация file_id для всех файлов заданий...")
        
        # Получаем все файлы заданий
        all_tasks = self._get_all_task_files()
        
        if not all_tasks:
            logger.warning("❌ Файлы заданий не найдены в папке tasks")
            return {}
        
        logger.info(f"📋 Найдено {len(all_tasks)} файлов заданий для обработки")
        
        file_ids = {}
        
        for i, task_name in enumerate(all_tasks, 1):
            task_path = self._find_task_file(task_name)
            if not task_path:
                logger.warning(f"Файл для задания {task_name} не найден")
                continue
                
            logger.info(f"📤 Отправка {i}/{len(all_tasks)}: {task_name}")
            
            file_id = await self._send_document_and_get_file_id(task_path, task_name)
            
            if file_id:
                file_ids[task_name] = file_id
                
            # Задержка между отправками
            await asyncio.sleep(0.5)
        
        # Сохраняем все file_id
        self._save_file_ids(file_ids)
        
        logger.info(f"✅ Регенерация завершена. Обработано {len(file_ids)} файлов заданий")
        return file_ids
    
    def get_file_id(self, task_name: str) -> Optional[str]:
        """Получить file_id для конкретного файла задания"""
        file_ids = self._load_existing_file_ids()
        return file_ids.get(task_name)
    
    def get_all_file_ids(self) -> Dict[str, str]:
        """Получить все file_id"""
        return self._load_existing_file_ids()


async def startup_task_files_check(bot: Bot, tasks_dir: str = "app/bot/assets/tasks", 
                                  target_chat_id: int = 257026813, 
                                  file_id_storage_path: str = "config/task_file_ids.json") -> Dict[str, str]:
    """
    Функция для проверки новых файлов заданий при старте бота.
    
    Args:
        bot: Экземпляр бота
        tasks_dir: Путь к папке с файлами заданий
        target_chat_id: ID чата для отправки файлов
        file_id_storage_path: Путь к файлу с file_id
        
    Returns:
        Словарь с file_id всех файлов заданий
    """
    manager = TaskFileIdManager(bot, tasks_dir, file_id_storage_path, target_chat_id)
    return await manager.check_and_upload_new_tasks()