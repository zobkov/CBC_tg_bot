"""
Middleware для админской блокировки бота
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.fsm.storage.redis import RedisStorage

logger = logging.getLogger(__name__)

LOCK_KEY = "bot:lock_mode"


class AdminLockMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int], storage: RedisStorage):
        self.admin_ids = set(admin_ids)
        self.storage = storage
        logger.info(f"AdminLockMiddleware is initialized with admins: {admin_ids}")
    
    async def is_lock_enabled(self) -> bool:
        try:
            redis = self.storage.redis
            result = await redis.get(LOCK_KEY)
            return result == b"1" if result else False
        except Exception as e:
            logger.error(f"Error checking for admin lock: {e}")
            return False
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Get user from update
        user = None
        
        # Check different update types
        if hasattr(event, 'message') and event.message and hasattr(event.message, 'from_user'):
            user = event.message.from_user
        elif hasattr(event, 'callback_query') and event.callback_query and hasattr(event.callback_query, 'from_user'):
            user = event.callback_query.from_user
        elif hasattr(event, 'inline_query') and event.inline_query and hasattr(event.inline_query, 'from_user'):
            user = event.inline_query.from_user
        elif hasattr(event, 'from_user') and event.from_user:
            user = event.from_user
        
        if not user:
            logger.debug(f"Нет пользователя в событии {type(event).__name__}")
            return await handler(event, data)
        
        user_id = user.id
        username = user.username
        
        # Logging 
        message_text = "Unknown"
        if hasattr(event, 'message') and event.message and hasattr(event.message, 'text'):
            message_text = event.message.text
        elif hasattr(event, 'callback_query') and event.callback_query and hasattr(event.callback_query, 'data'):
            message_text = f"callback: {event.callback_query.data}"
        
        logger.debug(f"Middleware: processing user id={user_id} @{username}, message: {message_text}")
        

        lock_enabled = await self.is_lock_enabled()
        logger.debug(f"AdminLockMiddleware: lock status = {lock_enabled}")
        
        # No lock – go further
        if not lock_enabled:
            logger.debug(f"Пользователь {user_id} проходит - блокировка выключена, сообщение: {message_text}")
            return await handler(event, data)
        

        is_admin = user_id in self.admin_ids
        
        if is_admin:
            # Admin – go
            logger.debug(f"Админ {user_id} проходит - режим блокировки включен")
            return await handler(event, data)
        
        # No admin? Go f yourself
        logger.info(f"ADMIN LOCK — {user_id} (@{user.username}) update dropped. Admin lock is on.")
        

        # Send lock message
        message_to_answer = None
        callback_to_answer = None
        

        if hasattr(event, 'message') and event.message:
            message_to_answer = event.message
        elif hasattr(event, 'callback_query') and event.callback_query:
            callback_to_answer = event.callback_query
        
        if callback_to_answer:
            await callback_to_answer.answer(
                "🔒 Бот временно заблокирован для технических работ. Попробуйте позже.",
                show_alert=True
            )
        elif message_to_answer:
            await message_to_answer.answer(
                "🔒 Бот временно заблокирован для технических работ.\n"
                "Попробуйте позже."
            )
        
        # Drop update
        return None


async def set_lock_mode(storage: RedisStorage, enabled: bool) -> bool:
    try:
        redis = storage.redis
        if enabled:
            await redis.set(LOCK_KEY, "1") # enabled
            logger.debug("Lock status in Redis: 1")
        else:
            await redis.set(LOCK_KEY, "0") # disabled
            logger.debug("Lock status in Redis: 0")
        return True
    except Exception as e:
        logger.error(f"Excpetion while setting admin lock status in Redis: {e}")
        return False


async def is_lock_mode_enabled(storage: RedisStorage) -> bool:
    try:
        redis = storage.redis
        result = await redis.get(LOCK_KEY)
        logger.debug(f"Redis value for key {LOCK_KEY}: {result} (type: {type(result)})")
        is_enabled = result == b"1" if result else False
        logger.debug(f"Admin lock enabled: {is_enabled}")
        return is_enabled
    except Exception as e:
        logger.error(f"Exception while checking admin lock status: {e}")
        return False