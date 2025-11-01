import asyncio
import logging

import psycopg_pool

from redis.asyncio import Redis

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.error_handler import ErrorHandlerMiddleware
from app.bot.middlewares.rbac import UserCtxMiddleware

from app.bot.handlers.commands import router as commands_router 
from app.bot.handlers.feedback_callbacks import feedback_callbacks_router 
from app.bot.handlers.admin_lock import setup_admin_commands_router
from app.bot.middlewares.admin_lock import AdminLockMiddleware 

# Импортируем роутеры для системы ролей
from app.bot.routers import (
    public_router,
    guest_router,
    volunteer_router, 
    staff_router,
    admin_router
)

# Импортируем валидатор доступа для диалогов
from app.bot.dialogs.access import RolesAccessValidator, create_forbidden_handler, create_forbidden_filter

# Импортируем систему аудита
from app.utils.audit import init_auditor

from app.bot.keyboards.command_menu import set_main_menu

from app.bot.dialogs.legacy.test.dialogs import test_dialog
from app.bot.dialogs.legacy.start.dialogs import start_dialog
from app.bot.dialogs.legacy.main_menu.dialogs import main_menu_dialog
from app.bot.dialogs.legacy.first_stage.dialogs import first_stage_dialog
from app.bot.dialogs.legacy.job_selection.dialogs import job_selection_dialog
from app.bot.dialogs.legacy.tasks.dialogs import task_dialog
from app.bot.dialogs.legacy.interview.dialogs import interview_dialog
from app.bot.dialogs.legacy.feedback.dialogs import feedback_dialog

# Новые role-based диалоги
from app.bot.dialogs.guest.dialogs import guest_menu_dialog
from app.bot.dialogs.guest.quiz_dod.dialogs import quiz_dod_dialog
from app.bot.dialogs.volunteer.dialogs import volunteer_menu_dialog  
from app.bot.dialogs.staff.dialogs import staff_menu_dialog

from app.services.broadcast_scheduler import BroadcastScheduler
from app.services.photo_file_id_manager import startup_photo_check
from pathlib import Path
from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)


async def main():
    logger.info("Loading config")
    config = load_config()

    logger.info("Starting bot")
    
    # Инициализируем переменные для корректного закрытия соединений
    redis_client = None
    db_applications_pool = None

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Иннициализируем redis
    logger.info("Connecting to Redis...")
    try:
        if config.redis.password:
            redis_url = f"redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/0"
            logger.info(f"Connecting to Redis with password at {config.redis.host}:{config.redis.port}")
            redis_client = Redis.from_url(redis_url, decode_responses=False)
        else:
            redis_url = f"redis://{config.redis.host}:{config.redis.port}/0"
            logger.info(f"Connecting to Redis without password at {config.redis.host}:{config.redis.port}")
            redis_client = Redis.from_url(redis_url, decode_responses=False)
        
        # Проверяем подключение к Redis
        logger.info("Testing Redis connection...")
        ping_result = await redis_client.ping()
        logger.info(f"Redis ping result: {ping_result}")
        logger.info(f"Successfully connected to Redis at {config.redis.host}:{config.redis.port}")
        
        # Создаем storage для FSM
        logger.info("Creating Redis storage for FSM...")
        storage = RedisStorage(
            redis=redis_client,
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
            state_ttl=86400,  # время жизни состояния в секунду (например, 1 день)
            data_ttl=86400   # время жизни данных
        )
        logger.info("Redis storage created successfully")
        
    except ConnectionError as e:
        logger.error(f"Connection error to Redis at {config.redis.host}:{config.redis.port}: {e}")
        logger.error("Check if Redis server is running and accessible")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to Redis at {config.redis.host}:{config.redis.port}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("Bot cannot start without Redis connection")
        raise

    dp = Dispatcher(storage=storage)
    
    # Добавляем конфигурацию в диспетчер
    dp["config"] = config
    dp["bot"] = bot
    
    # Подключение к базе данных заявок
    db_applications_pool = await get_pg_pool(
        db_name=config.db_applications.database,
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password,
    )
    dp["db_applications"] = db_applications_pool
    # Пул для обратной совместимости ключа db
    dp["db"] = db_applications_pool

    logger.info("Including routers")
    
    # Настраиваем админские команды
    admin_commands_router = setup_admin_commands_router(config.admin_ids)
    
    # Подключаем роутеры системы ролей (в правильном порядке приоритета)
    dp.include_routers(
        admin_commands_router,  # Команды админов /lock /unlock /status
        public_router,          # Публичные команды (/start, /help, /whoami)
        admin_router,           # Админские команды и функции
        staff_router,           # Функции для сотрудников
        volunteer_router,       # Функции для волонтёров  
        guest_router,           # Функции для гостей
        commands_router,        # Существующие команды (legacy)
        feedback_callbacks_router
    )
    
    dp.include_routers(
        test_dialog,
        start_dialog,
        main_menu_dialog,
        first_stage_dialog,
        job_selection_dialog,
        task_dialog,
        interview_dialog,
        feedback_dialog,
        # Новые role-based диалоги
        guest_menu_dialog,
    quiz_dod_dialog,
        volunteer_menu_dialog,
        staff_menu_dialog
                       )

    logger.info("Including middlewares")
    # Добавляем middleware блокировки ПЕРВЫМ (ДО всех остальных)
    dp.update.middleware(AdminLockMiddleware(config.admin_ids, storage))
    
    # Инициализируем аудитор для RBAC
    init_auditor(redis=redis_client)
    
    # Создаем middleware для ролей
    user_ctx_middleware = UserCtxMiddleware(redis=redis_client)
    
    # Добавляем middleware для ролей ПОСЛЕ DatabaseMiddleware
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(user_ctx_middleware)
    
    # Debug middleware для проверки после всех middleware
    @dp.update.middleware()
    async def post_dialog_debug_middleware(handler, event, data):
        # Добавляем ссылку на UserCtxMiddleware и Redis в контекст
        data["user_ctx_middleware"] = user_ctx_middleware
        data["redis"] = redis_client
        result = await handler(event, data)
        return result

    logger.info("Setting up dialogs")
    # Настраиваем валидатор доступа для диалогов (по умолчанию разрешает всем кроме banned)
    access_validator = RolesAccessValidator()
    bg_factory = setup_dialogs(dp, stack_access_validator=access_validator)
    
    # Добавляем обработчик запрещенного доступа к диалогам с фильтром
    forbidden_handler = create_forbidden_handler()
    forbidden_filter = create_forbidden_filter()
    dp.message.register(forbidden_handler, forbidden_filter)

    await set_main_menu(bot)

    # Проверяем новые фотографии и обновляем file_id при старте
    logger.info("Checking for new photos and updating file_ids...")
    try:
        file_ids = await startup_photo_check(bot)
        logger.info(f"Photo file_id check completed. Total photos: {len(file_ids)}")
    except Exception as e:
        logger.error(f"Error during photo file_id check: {e}")
        # Не останавливаем бота из-за ошибки с фотографиями

    # Проверяем новые файлы заданий и обновляем file_id при старте
    logger.info("Checking for new task files and updating file_ids...")
    try:
        from app.services.task_file_id_manager import startup_task_files_check
        task_file_ids = await startup_task_files_check(bot)
        logger.info(f"Task file_id check completed. Total task files: {len(task_file_ids)}")
    except Exception as e:
        logger.error(f"Error during task file_id check: {e}")
        # Не останавливаем бота из-за ошибки с файлами заданий

    # Launch polling and broadcast scheduler
    try:
        scheduler = BroadcastScheduler(
            bot=bot,
            db_pool=db_applications_pool,
            json_path=Path("config/broadcasts.json")
        )
        await scheduler.start()
        await bot.delete_webhook(drop_pending_updates=True)
        
        await dp.start_polling(
            bot,
            bg_factory=bg_factory,
            _db_applications_pool=db_applications_pool,
        )
    except Exception as e:
        logger.exception(e)
    finally:
        try:
            await scheduler.stop()  # type: ignore
        except Exception:
            pass
        
        # Закрываем соединение с Redis
        if redis_client:
            try:
                await redis_client.aclose()
                logger.info("Connection to Redis closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        
        # Закрываем соединение с Postgres
        if db_applications_pool:
            try:
                await db_applications_pool.close()
                logger.info("Connection to Postgres closed")
            except Exception as e:
                logger.error(f"Error closing Postgres connection: {e}")
