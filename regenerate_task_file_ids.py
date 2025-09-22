#!/usr/bin/env python3
"""
Скрипт для генерации file_id файлов заданий
"""
import asyncio
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.config import load_config
from app.services.task_file_id_manager import TaskFileIdManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def regenerate_task_file_ids():
    """Регенерирует file_id для всех файлов заданий"""
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Создаем бота
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    try:
        # Создаем менеджер
        manager = TaskFileIdManager(
            bot=bot,
            tasks_dir="app/bot/assets/tasks",
            file_id_storage_path="config/task_file_ids.json", 
            target_chat_id=257026813
        )
        
        # Генерируем file_id
        logger.info("🚀 Начинаем генерацию file_id для файлов заданий...")
        file_ids = await manager.regenerate_all_file_ids()
        
        logger.info(f"✅ Генерация завершена! Обработано {len(file_ids)} файлов:")
        for task_name, file_id in file_ids.items():
            logger.info(f"  📋 {task_name}: {file_id}")
            
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(regenerate_task_file_ids())