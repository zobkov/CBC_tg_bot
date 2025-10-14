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
    """Middleware для блокировки не-админов во время технических работ"""
    
    def __init__(self, admin_ids: list[int], storage: RedisStorage):
        self.admin_ids = set(admin_ids)
        self.storage = storage
        logger.info(f"AdminLockMiddleware инициализирован с админами: {admin_ids}")
    
    async def is_lock_enabled(self) -> bool:
        """Проверяет, включен ли режим блокировки"""
        try:
            redis = self.storage.redis
            result = await redis.get(LOCK_KEY)
            return result == b"1" if result else False
        except Exception as e:
            logger.error(f"Ошибка при проверке режима блокировки: {e}")
            return False
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Основная логика middleware"""
        
        # Получаем пользователя из события
        user = None
        
        # Проверяем разные типы событий в Update
        if hasattr(event, 'message') and event.message and hasattr(event.message, 'from_user'):
            user = event.message.from_user
        elif hasattr(event, 'callback_query') and event.callback_query and hasattr(event.callback_query, 'from_user'):
            user = event.callback_query.from_user
        elif hasattr(event, 'inline_query') and event.inline_query and hasattr(event.inline_query, 'from_user'):
            user = event.inline_query.from_user
        elif hasattr(event, 'from_user') and event.from_user:
            user = event.from_user
        
        if not user:
            # Если нет пользователя, пропускаем дальше
            logger.debug(f"Нет пользователя в событии {type(event).__name__}")
            return await handler(event, data)
        
        user_id = user.id
        logger.debug(f"Middleware: обрабатываем пользователя {user_id}")
        
        # Проверяем режим блокировки
        lock_enabled = await self.is_lock_enabled()
        logger.debug(f"Middleware: режим блокировки = {lock_enabled}")
        
        if not lock_enabled:
            # Блокировка выключена - пропускаем дальше
            logger.debug(f"Пользователь {user_id} проходит - блокировка выключена")
            return await handler(event, data)
        
        # Блокировка включена - проверяем админа
        is_admin = user_id in self.admin_ids
        logger.debug(f"Пользователь {user_id} админ: {is_admin}")
        
        if is_admin:
            # Админ - пропускаем дальше
            logger.debug(f"Админ {user_id} проходит - режим блокировки включен")
            return await handler(event, data)
        
        # Не-админ при включенной блокировке - блокируем
        logger.warning(f"🚫 ЗАБЛОКИРОВАН пользователь {user_id} (@{user.username}) - режим блокировки включен")
        
        # Отправляем сообщение о блокировке
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
        
        # Не вызываем следующий хендлер
        return None


async def set_lock_mode(storage: RedisStorage, enabled: bool) -> bool:
    """Устанавливает режим блокировки"""
    try:
        redis = storage.redis
        if enabled:
            await redis.set(LOCK_KEY, "1")
            logger.info("Режим блокировки установлен в Redis: 1")
        else:
            await redis.set(LOCK_KEY, "0")
            logger.info("Режим блокировки установлен в Redis: 0")
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке режима блокировки: {e}")
        return False


async def is_lock_mode_enabled(storage: RedisStorage) -> bool:
    """Проверяет, включен ли режим блокировки"""
    try:
        redis = storage.redis
        result = await redis.get(LOCK_KEY)
        logger.debug(f"Значение в Redis для ключа {LOCK_KEY}: {result} (тип: {type(result)})")
        is_enabled = result == b"1" if result else False
        logger.debug(f"Режим блокировки включен: {is_enabled}")
        return is_enabled
    except Exception as e:
        logger.error(f"Ошибка при проверке режима блокировки: {e}")
        return False