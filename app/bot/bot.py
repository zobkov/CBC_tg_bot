"""
Main app module. Telegram bot polling entrypoint
"""
from __future__ import annotations

import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs

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

from app.bot.handlers.feedback_callbacks import feedback_callbacks_router
from app.bot.handlers.admin_lock import setup_admin_lock_router
from app.bot.middlewares.admin_lock import AdminLockMiddleware

# Roles routers
from app.bot.routers import (
    public_router,
    guest_router,
    volunteer_router,
    staff_router,
    admin_router,
)

from app.bot.dialogs.access import (
    RolesAccessValidator,
    create_forbidden_filter,
    create_forbidden_handler,
)


from app.utils.audit import init_auditor


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

from app.bot.dialogs.broadcasts.dialogs import broadcast_menu_dialog
from app.bot.dialogs.selections.creative import creative_selection_dialog

from app.services.photo_file_id_manager import startup_photo_check
from app.services.task_file_id_manager import startup_task_files_check

logger = logging.getLogger(__name__)


async def _init_redis_storage(config):
    """Create Redis client and FSM storage with connection checks."""
    logger.info("Connecting to Redis...")
    try:
        if config.redis.password:
            redis_url = (
                f"redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/0"
            )
            logger.debug(
                "Connecting to Redis with password at %s:%s",
                config.redis.host,
                config.redis.port,
            )
        else:
            redis_url = f"redis://{config.redis.host}:{config.redis.port}/0"
            logger.debug(
                "Connecting to Redis without password at %s:%s",
                config.redis.host,
                config.redis.port,
            )

        redis_client = Redis.from_url(redis_url, decode_responses=False)

        # Connection test to Redis
        logger.info("Testing Redis connection...")
        ping_result = await redis_client.ping()
        logger.info("Redis ping result: %s", ping_result)
        logger.info(
            "Successfully connected to Redis at %s:%s",
            config.redis.host,
            config.redis.port,
        )

        storage = RedisStorage(
            redis=redis_client,
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
            state_ttl=86400,  # FSM state life (seconds)
            data_ttl=86400,  # date life (seconds)
        )
        logger.info("Redis FSM storage created successfully")
        return redis_client, storage

    except ConnectionError as exc:
        logger.error(
            "Connection error to Redis at %s:%s: %s",
            config.redis.host,
            config.redis.port,
            exc,
        )
        logger.error("Check if Redis server is running and accessible")
        logger.critical("Bot cannot start without Redis connection. Shutdown")
        raise
    except RedisError as exc:  # pragma: no cover - infrastructure failures
        logger.error(
            "Failed to connect to Redis at %s:%s: %s",
            config.redis.host,
            config.redis.port,
            exc,
        )
        logger.error("Error type: %s", type(exc).__name__)
        logger.critical("Bot cannot start without Redis connection. Shutdown")
        raise


async def _init_database(config, redis_client):
    """Ensure SQLAlchemy engine and session factory are ready."""
    db_cfg = config.db
    missing_db_fields = [
        field_name
        for field_name in ("host", "port", "database", "user", "password")
        if not getattr(db_cfg, field_name, None)
    ]
    if missing_db_fields:
        logger.critical(
            "Database configuration is missing values: %s",
            ", ".join(missing_db_fields),
        )
        raise RuntimeError("Incomplete database configuration; aborting startup")

    try:
        get_engine()
        session_factory = get_session_factory()
        logger.info("SQLAlchemy session factory initialised successfully")

        logger.info("Running database connectivity healthcheck...")
        if not await healthcheck():
            raise RuntimeError("Database healthcheck returned False")
        logger.info("Database connectivity check succeeded")
        return session_factory

    except Exception as db_exc:  # pragma: no cover - startup failures
        logger.exception(
            "Database initialisation failed. Verify credentials, network access, and that the DB"
            " is reachable",
        )
        if redis_client:
            try:
                await redis_client.aclose()
                logger.info(
                    "Redis connection closed after database initialisation failure",
                )
            except RedisError as close_exc:  # pragma: no cover - protective logging
                logger.warning(
                    "Failed to close Redis connection during error handling: %s",
                    close_exc,
                )
        raise db_exc


def _configure_dispatcher(
    config,
    bot,
    redis_client,
    session_factory,
    storage,
) -> tuple[Dispatcher, Any]:
    """Wire routers, middlewares, and dialog stack for the dispatcher."""
    dp = Dispatcher(storage=storage)

    # Pass shared resources through dispatcher context
    dp["config"] = config
    dp["bot"] = bot
    dp["redis"] = redis_client
    dp["db_session_factory"] = session_factory

    logger.info("Including routers")

    admin_lock_router = setup_admin_lock_router(config.admin_ids)

    dp.include_routers(
        admin_lock_router,
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
        broadcast_menu_dialog,
        creative_selection_dialog,
    )

    dp.include_routers(
        admin_router,
        staff_router,
        volunteer_router,
        guest_router,
        feedback_callbacks_router,
    )

    logger.info("Including middlewares")
    dp.update.middleware(AdminLockMiddleware(config.admin_ids, storage))

    init_auditor(redis=redis_client)

    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(DatabaseMiddleware())

    user_ctx_middleware = UserCtxMiddleware(redis=redis_client)
    dp["user_ctx_middleware"] = user_ctx_middleware
    dp.update.middleware(user_ctx_middleware)

    access_validator = RolesAccessValidator()
    bg_factory = setup_dialogs(dp, stack_access_validator=access_validator)

    forbidden_handler = create_forbidden_handler()
    forbidden_filter = create_forbidden_filter()
    dp.message.register(forbidden_handler, forbidden_filter)

    return dp, bg_factory


async def main():
    """Configure dependencies and run the Telegram bot polling loop."""
    logger.info("Loading config")
    config = load_config()

    logger.info("Starting bot")

    redis_client = None

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    redis_client, storage = await _init_redis_storage(config)
    session_factory = await _init_database(config, redis_client)

    dp, bg_factory = _configure_dispatcher(
        config=config,
        bot=bot,
        redis_client=redis_client,
        session_factory=session_factory,
        storage=storage,
    )

    # await set_main_menu(bot) is deprecated. Use botfather app instead

    # ––– PHOTO FILE_ID CHECK
    logger.info("Checking for new photos and updating file_ids...")
    try:
        logger.info(
            "Photo file_id check completed. Total photos: %d",
            len(await startup_photo_check(bot)),
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error during photo file_id check: %s", exc)


    # ––– TASK FILE_ID CHECK (LEGACY)
    logger.info("Checking for new task files and updating file_ids...")
    try:
        logger.info(
            "Task file_id check completed. Total task files: %d",
            len(await startup_task_files_check(bot)),
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error during task file_id check: %s", exc)

    # ––– SCHEDULER SETUP (Creative Google Sheets Sync)
    logger.info("Setting up scheduled tasks...")
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.services.creative_google_sync import CreativeGoogleSheetsSync
        from app.infrastructure.database.database.db import DB

        scheduler = AsyncIOScheduler()

        async def scheduled_creative_google_sync():
            """Runs hourly to sync creative applications to Google Sheets."""
            try:
                async with session_factory() as session:
                    db = DB(session)
                    sync_service = CreativeGoogleSheetsSync(db)
                    count = await sync_service.sync_all_applications()
                    logger.info(
                        "[SCHEDULED] Synced %d creative applications to Google Sheets",
                        count,
                    )
            except Exception as e:
                logger.error(
                    "[SCHEDULED] Failed to sync creative applications: %s",
                    e,
                    exc_info=True,
                )

        # Schedule hourly sync
        scheduler.add_job(
            scheduled_creative_google_sync,
            "interval",
            hours=1,
            id="creative_google_sync",
        )

        scheduler.start()
        logger.info("✅ Scheduled creative Google Sheets sync (hourly)")

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to set up scheduler: %s", exc)

    # Launch polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)

        await dp.start_polling(
            bot,
            bg_factory=bg_factory,
            db_session_factory=session_factory,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unhandled error while polling: %s", exc)
    finally:
        if redis_client:
            try:
                await redis_client.aclose()
                logger.info("Connection to Redis closed")
            except RedisError as exc:
                logger.error("Error closing Redis connection: %s", exc)

        try:
            await dispose_engine()
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.error("Error disposing SQLAlchemy engine: %s", exc)
