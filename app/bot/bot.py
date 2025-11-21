import asyncio
import logging

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
from app.infrastructure.database.sqlalchemy_core import (
    dispose_engine,
    get_engine,
    get_session_factory,
    healthcheck,
)
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.error_handler import ErrorHandlerMiddleware
from app.bot.middlewares.rbac import UserCtxMiddleware

from app.bot.handlers.commands import router as commands_router 
from app.bot.handlers.feedback_callbacks import feedback_callbacks_router 
from app.bot.handlers.admin_lock import setup_admin_commands_router
from app.bot.middlewares.admin_lock import AdminLockMiddleware 

# Roles routers
from app.bot.routers import (
    public_router,
    guest_router,
    volunteer_router, 
    staff_router,
    admin_router
)

from app.bot.dialogs.access import RolesAccessValidator, create_forbidden_handler, create_forbidden_filter


from app.utils.audit import init_auditor

from app.bot.keyboards.command_menu import set_main_menu

from app.bot.dialogs.legacy.test.dialogs import test_dialog
from app.bot.dialogs.legacy.start.dialogs import start_dialog
from app.bot.dialogs.legacy.main_menu.dialogs import main_menu_dialog
from app.bot.dialogs.legacy.first_stage.dialogs import first_stage_dialog
from app.bot.dialogs.legacy.job_selection.dialogs import job_selection_dialog
from app.bot.dialogs.legacy.tasks.dialogs import task_dialog
from app.bot.dialogs.legacy.interview.dialogs import interview_dialog

from app.bot.dialogs.guest.dialogs import guest_menu_dialog
from app.bot.dialogs.guest.feedback import feedback_dialog
from app.bot.dialogs.guest.quiz_dod.dialogs import quiz_dod_dialog
from app.bot.dialogs.volunteer.dialogs import volunteer_menu_dialog  
from app.bot.dialogs.staff.dialogs import staff_menu_dialog

from app.services.broadcast_scheduler import BroadcastScheduler
from app.services.photo_file_id_manager import startup_photo_check
from pathlib import Path

logger = logging.getLogger(__name__)


async def main():
    logger.info("Loading config")
    config = load_config()

    logger.info("Starting bot")
    
    redis_client = None

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # redis init
    logger.info("Connecting to Redis...")
    try:
        if config.redis.password:
            redis_url = f"redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/0"
            logger.debug(f"Connecting to Redis with password at {config.redis.host}:{config.redis.port}")
            redis_client = Redis.from_url(redis_url, decode_responses=False)
        else:
            redis_url = f"redis://{config.redis.host}:{config.redis.port}/0"
            logger.debug(f"Connecting to Redis without password at {config.redis.host}:{config.redis.port}")
            redis_client = Redis.from_url(redis_url, decode_responses=False)
        
        # Connection test to Redis
        logger.info("Testing Redis connection...")
        ping_result = await redis_client.ping()
        logger.info(f"Redis ping result: {ping_result}")
        logger.info(f"Successfully connected to Redis at {config.redis.host}:{config.redis.port}")
        
        storage = RedisStorage(
            redis=redis_client,
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
            state_ttl=86400,  # FSM state life (seconds)
            data_ttl=86400   # date life (seconds)
        )
        logger.info("Redis FSM storage created successfully")
        
    except ConnectionError as e:
        logger.error(f"Connection error to Redis at {config.redis.host}:{config.redis.port}: {e}")
        logger.error("Check if Redis server is running and accessible")
        logger.critical("Bot cannot start without Redis connection. Shutdown")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to Redis at {config.redis.host}:{config.redis.port}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.critical("Bot cannot start without Redis connection. Shutdown")
        raise

    db_cfg = config.db

    missing_db_fields = [
        field_name
        for field_name in ("host", "port", "database", "user", "password")
        if not getattr(db_cfg, field_name, None)
    ]
    if missing_db_fields:
        logger.critical("Database configuration is missing values: %s", ", ".join(missing_db_fields))
        raise RuntimeError("Incomplete database configuration; aborting startup")

    try:
        engine = get_engine()
        
        session_factory = get_session_factory()
        logger.info("SQLAlchemy session factory initialised successfully")

        logger.info("Running database connectivity healthcheck...")
        db_ok = await healthcheck()
        if not db_ok:
            raise RuntimeError("Database healthcheck returned False")
        logger.info("Database connectivity check succeeded")
    except Exception as db_exc:
        logger.exception(
            "Database initialisation failed. Verify credentials, network access, and that the DB is reachable"
        )
        if redis_client:
            try:
                await redis_client.aclose()
                logger.info("Redis connection closed after database initialisation failure")
            except Exception as close_exc:  # pragma: no cover - protective logging
                logger.warning("Failed to close Redis connection during error handling: %s", close_exc)
        raise

    dp = Dispatcher(storage=storage)
    
    # Pass configs to dispatcher
    dp["config"] = config
    dp["bot"] = bot
    dp["redis"] = redis_client
    dp["db_session_factory"] = session_factory

    logger.info("Including routers")
    
    admin_commands_router = setup_admin_commands_router(config.admin_ids)

    # The order of router registry is crucial
    # First registered – first checked when update comes

    dp.include_routers(
        admin_commands_router,  # Admin commands /lock /unlock /status /ch_roles
        public_router,      
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
        guest_menu_dialog,
        quiz_dod_dialog,
        volunteer_menu_dialog,
        staff_menu_dialog,
    )

    # 
    dp.include_routers(
        admin_router,           
        staff_router,           # Staff
        volunteer_router,       
        guest_router,           # Guests
        
        # here broadcasting callbacks can be placed as they are very specific
        feedback_callbacks_router, 
    )

    logger.info("Including middlewares")

    # First is ALWAYS lock middleware
    dp.update.middleware(AdminLockMiddleware(config.admin_ids, storage))
    
    init_auditor(redis=redis_client)
    

    
    
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(DatabaseMiddleware())

    # Role middleware – must be init after DB mw
    user_ctx_middleware = UserCtxMiddleware(redis=redis_client)
    dp["user_ctx_middleware"] = user_ctx_middleware

    dp.update.middleware(user_ctx_middleware)
    

    # Access validator
    access_validator = RolesAccessValidator()
    bg_factory = setup_dialogs(dp, stack_access_validator=access_validator)
    
    forbidden_handler = create_forbidden_handler()
    forbidden_filter = create_forbidden_filter()
    dp.message.register(forbidden_handler, forbidden_filter)

    # await set_main_menu(bot) is deprecated. Use botfather app instead

    # ––– PHOTO FILE_ID CHECK
    logger.info("Checking for new photos and updating file_ids...")
    try:
        file_ids = await startup_photo_check(bot)
        logger.info(f"Photo file_id check completed. Total photos: {len(file_ids)}")
    except Exception as e:
        logger.error(f"Error during photo file_id check: {e}")


    # ––– TASK FILE_ID CHECK (LEGACY)
    logger.info("Checking for new task files and updating file_ids...")
    try:
        from app.services.task_file_id_manager import startup_task_files_check
        task_file_ids = await startup_task_files_check(bot)
        logger.info(f"Task file_id check completed. Total task files: {len(task_file_ids)}")
    except Exception as e:
        logger.error(f"Error during task file_id check: {e}")


    # Launch polling and broadcast scheduler (TODO)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        
        await dp.start_polling(
            bot,
            bg_factory=bg_factory,
            db_session_factory=session_factory,
        )
    except Exception as e:
        logger.exception(e)
    finally:
        
        if redis_client:
            try:
                await redis_client.aclose()
                logger.info("Connection to Redis closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        
        try:
            await dispose_engine()
        except Exception as e:
            logger.error(f"Error disposing SQLAlchemy engine: {e}")
