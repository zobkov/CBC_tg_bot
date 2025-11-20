"""
Middleware для работы с контекстом пользователя и ролями
"""
import json
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, User

from app.infrastructure.database.models.users import UsersModel
from app.utils.telegram import get_event_user
from app.enums.roles import Role

logger = logging.getLogger(__name__)


class UserCtxMiddleware(BaseMiddleware):
    """
    Middleware for loading user context and role

    Gets roles from Redis cache
    Drops banned users' updates
    Passes current_user and roles to handlers
    """

    def __init__(self, redis=None):
        self.redis = redis
        self.cache_ttl = 60*5  # Cache life

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Основной обработчик middleware
        
        Args:
            handler: Следующий обработчик в цепочке
            event: Telegram событие
            data: Данные контекста
            
        Returns:
            Результат выполнения обработчика или None для заблокированных пользователей
        """
        user: User = get_event_user(event)
        if not user:
            # With no user in an update – skip mw
            return await handler(event, data)

        # Get DB from context
        db = data.get("db")
        if not db:
            logger.warning("Database not found in middleware context")
            return await handler(event, data)

        try:
            # Get user with roles from cache or DB
            user = await self._load_user_with_roles(user, db)
            
            roles = set(user.roles) if user else {Role.GUEST.value}
            
            data["current_user"] = user
            data["roles"] = roles  
            
            # Drop banned users' update
            if Role.BANNED.value in roles:
                await self._handle_banned_user(event)
                return None  
            

            logger.debug(f"UserCtxMiddleware: user id={user.id} @{user.username} — roles: {list(data['roles'])}")
            
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Error in UserCtxMiddleware for user {user.id}: {e}")
            # Set default value 
            data["current_user"] = None
            data["roles"] = {Role.GUEST.value} 
            return await handler(event, data)

    async def _load_user_with_roles(self, user_tg: User, db) -> UsersModel | None:
        """
        Load user info either from cache or DB
        """
        user_id = user_tg.id

        cache_key = f"rbac:{user_id}"
        user = None
        
        # Try to get from cache
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    if isinstance(cached_data, (bytes, bytearray)):
                        cached_data = cached_data.decode("utf-8")
                    user = UsersModel.from_cache(json.loads(cached_data))
                    logger.debug(f"User {user_id} loaded from cache")
            except Exception as e:
                logger.debug(f"Failed to load user {user_id} from cache: {e}")
        
        # Try to get from DB
        if not user:
            try:
                user = await db.users.get_user_record(user_id=user_id)
            except Exception as e:
                logging.exception(f"Failed to get user id={user_id} @{user_tg.username} from DB")
            
            # Save to cache
            if user and self.redis:
                try:
                    # Serialize for cache
                    payload = json.dumps(user.to_cache_dict(), default=str)
                    await self.redis.setex(cache_key, self.cache_ttl, payload)
                    logger.debug(f"User {user_id} cached for {self.cache_ttl}s")
                except Exception as e:
                    logger.warning(f"Failed to cache user {user_id}: {e}")
        
        return user


    async def _handle_banned_user(self, event: TelegramObject):
        # If message, answer 
        if isinstance(event, Message):
            try:
                await event.answer("⛔ Доступ запрещён.")
            except Exception as e:
                logger.warning(f"Failed to send ban message: {e}")
        
        # Log attmept to access by banned user
        user = get_event_user(event)
        if user:
            logger.warning(f"Banned user {user.id} (@{user.username}) tried to access bot")


    async def invalidate_user_cache(self, user_id: int):
        """
        Invalidates (deletes) user cache.
        Used for role changes. Change role in DB and invalidate it in cache. Less headache :)
        """
        if self.redis:
            try:
                cache_key = f"rbac:{user_id}"
                await self.redis.delete(cache_key)
                logger.debug(f"Cache invalidated for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache for user {user_id}: {e}")