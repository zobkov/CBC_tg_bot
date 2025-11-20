from typing import Callable, Dict, Any, Awaitable

import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для работы с базой данных"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        dispatcher = data.get("_dispatcher") or data.get("dispatcher") or data.get("dp")

        session_factory: async_sessionmaker[AsyncSession] | None = None
        bot = None
        config = None
        redis_client = None
        user_ctx_middleware = None

        if dispatcher:
            session_factory = dispatcher.get("db_session_factory")
            bot = dispatcher.get("bot")
            config = dispatcher.get("config")
            redis_client = dispatcher.get("redis")
            user_ctx_middleware = dispatcher.get("user_ctx_middleware")

        if session_factory is None:
            session_factory = data.get("db_session_factory")

        if bot is None:
            bot = data.get("bot")
        if config is None:
            config = data.get("config")
        if redis_client is None:
            redis_client = data.get("redis")
        if user_ctx_middleware is None:
            user_ctx_middleware = data.get("user_ctx_middleware")

        if session_factory is None:
            logger.warning("SQLAlchemy session factory not found in DatabaseMiddleware")
            return await handler(event, data)

        user: User | None = data.get("event_from_user")
        if not user:
            logger.debug("⚠️ Пользователь не найден в событии, пропускаем DatabaseMiddleware")
            return await handler(event, data)

        logger.debug("🔍 DatabaseMiddleware: обрабатываем пользователя %s (@%s)", user.id, user.username)
        try:
            async with session_factory() as session:
                async with session.begin():
                    database = DB(session=session)

                    logger.debug("🔍 Проверяем существование пользователя %s", user.id)
                    user_record = await database.users.get_user_record(user_id=user.id)

                    if not user_record:
                        logger.info("👤 Создаем нового пользователя: %s (@%s)", user.id, user.username)
                        await database.users.add(
                            user_id=user.id,
                            language=user.language_code or "ru",
                        )
                        logger.info("✅ Новый пользователь создан: %s", user.id)
                    else:
                        logger.debug("🔄 Обновляем статус активности пользователя %s", user.id)
                        await database.users.update_alive_status(user_id=user.id, is_alive=True)

                    data["db"] = database
                    if bot:
                        data["bot"] = bot
                    if config:
                        data["config"] = config
                    if redis_client:
                        data["redis"] = redis_client
                    if user_ctx_middleware:
                        data["user_ctx_middleware"] = user_ctx_middleware

                    logger.debug("🎯 Вызываем обработчик для пользователя %s", user.id)
                    result = await handler(event, data)

                logger.debug("✅ DatabaseMiddleware: обработка пользователя %s завершена", user.id)
                return result
        except Exception as exc:  # pragma: no cover
            logger.error("❌ Критическая ошибка в DatabaseMiddleware для пользователя %s: %s", user.id, exc)
            logger.error("📋 Тип события: %s", type(event).__name__)
            logger.error("📋 Данные события: %s", data)
            return await handler(event, data)
