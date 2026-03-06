from typing import Callable, Dict, Any, Awaitable

import logging
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, User

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.infrastructure.database.database.db import DB

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        
        # Get dispatcher 
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
            logger.debug("User not found in update, skip DatabaseMiddleware")
            return await handler(event, data)

        logger.debug("DatabaseMiddleware: processing user id=%s (@%s)", user.id, user.username)
        try:
            async with session_factory() as session:
                async with session.begin():
                    database = DB(session=session)

                    user_record = await database.users.get_user_record(user_id=user.id)

                    if not user_record:
                        logger.info("User not found, creating new one: id=%s (@%s)", user.id, user.username)
                        await database.users.add(
                            user_id=user.id,
                            roles=["guest"],
                        )
                        logger.info("New user created: id=%s, @%s", user.id, user.username)
                    else:
                        logger.debug("Update alive status user id=%s", user.id)
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

                    logger.debug("Hadnler call for id=%s", user.id)
                    result = await handler(event, data)

                return result
        except TelegramBadRequest as e:  # pragma: no cover
            if "message is too long" in str(e).lower():
                logger.warning("⚠️ Message too long in DatabaseMiddleware for id=%s: %s", user.id, e)
                _bot = bot or data.get("bot")
                _event_message = getattr(event, "message", None)
                _chat_id = (
                    _event_message.chat.id
                    if _event_message
                    else None
                )
                if _bot and _chat_id:
                    try:
                        await _bot.send_message(
                            chat_id=_chat_id,
                            text=(
                                "Упс! Это слишком длинное сообщение. "
                                "По правилам телеграма мы не можем его обработать. "
                                "Укороти его, пожалуйста, и отправь еще раз."
                            ),
                        )
                    except Exception as send_error:
                        logger.error("Failed to send 'message too long' notice to %s: %s", _chat_id, send_error)
                return None
            logger.error("❌ Error in DatabaseMIddleware for id=%s: %s", user.id, e)
            logger.error("📋 Update type: %s", type(event).__name__)
            logger.error("📋 Update data: %s", data)
            return await handler(event, data)
        except Exception as e:  # pragma: no cover
            logger.error("❌ Error in DatabaseMIddleware for id=%s: %s", user.id, e)
            logger.error("📋 Update type: %s", type(event).__name__)
            logger.error("📋 Update data: %s", data)
            return await handler(event, data)
