import asyncio
import logging

import psycopg_pool
import redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.bot.middlewares.database import DatabaseMiddleware

from app.bot.handlers.commands import router as commands_router 

from app.bot.keyboards.command_menu import set_main_menu

from app.bot.dialogs.test.dialogs import test_dialog
from app.bot.dialogs.start.dialogs import start_dialog
from app.bot.dialogs.main_menu.dialogs import main_menu_dialog
from app.bot.dialogs.first_stage.dialogs import first_stage_dialog
from app.bot.dialogs.job_selection.dialogs import job_selection_dialog

logger = logging.getLogger(__name__)


async def main():
    logger.info("Loading config")
    config = load_config()

    logger.info("Starting bot")

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher()
    
    # Добавляем конфигурацию в диспетчер
    dp["config"] = config
    dp["bot"] = bot
    
    # Подключение к базе данных пользователей
    db_pool: psycopg_pool.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db.database,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )
    dp["db"] = db_pool
    
    # Подключение к базе данных заявок
    db_applications_pool: psycopg_pool.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db_applications.database,
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password,
    )
    dp["db_applications"] = db_applications_pool

    logger.info("Including routers")
    dp.include_routers(
        commands_router
                       )
    
    dp.include_routers(
        test_dialog,
        start_dialog,
        main_menu_dialog,
        first_stage_dialog,
        job_selection_dialog
                       )

    logger.info("Including middlewares")
    dp.update.middleware(DatabaseMiddleware())

    logger.info("Setting up dialogs")
    bg_factory = setup_dialogs(dp)

    await set_main_menu(bot)

    # Launch polling and delayed message consumer
    try:
        await asyncio.gather(
            dp.start_polling(
                bot,
                bg_factory=bg_factory,
                _db_pool=db_pool,
                _db_applications_pool=db_applications_pool,
            ),
        )
    except Exception as e:
        logger.exception(e)
    finally:
        await db_pool.close()
        await db_applications_pool.close()
        logger.info("Connection to Postgres closed")
