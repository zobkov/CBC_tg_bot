"""
Middleware для работы с контекстом пользователя и ролями
"""
import json
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.infrastructure.database.models.users import UsersModel
from app.utils.telegram import get_event_user
from app.enums.roles import Role

logger = logging.getLogger(__name__)


class UserCtxMiddleware(BaseMiddleware):
    """
    Middleware для загрузки контекста пользователя и ролей.
    Обеспечивает:
    - Загрузку пользователя и его ролей из БД с кэшем в Redis
    - Раннюю отсечку заблокированных пользователей (BANNED роль)
    - Предоставление current_user и roles в контексте обработчиков
    """

    def __init__(self, redis=None):
        """
        Args:
            redis: Redis клиент для кэширования
        """
        self.redis = redis
        self.cache_ttl = 120  # TTL кэша 120 секунд

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
        tg_user = get_event_user(event)
        if not tg_user:
            # Если нет пользователя в событии, просто пропускаем дальше
            return await handler(event, data)

        # Получаем БД из контекста (должна быть установлена DatabaseMiddleware)
        db = data.get("db")
        if not db:
            logger.warning("Database not found in middleware context")
            return await handler(event, data)

        try:
            # Загружаем пользователя с ролями из кэша или БД
            user = await self._load_user_with_roles(tg_user.id, db)
            
            roles = set(user.roles) if user else {Role.GUEST.value}
            
            # Добавляем данные в контекст
            data["current_user"] = user
            data["roles"] = roles  # roles уже строки из БД
            
            # КРИТИЧНО: Ранняя отсечка BANNED пользователей
            if Role.BANNED.value in roles:
                await self._handle_banned_user(event)
                return  # Останавливаем обработку
            
            logger.debug(
                f"UserCtxMiddleware: пользователь {tg_user.id} с ролями {list(data['roles'])}"
            )
            
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Error in UserCtxMiddleware for user {tg_user.id}: {e}")
            # В случае ошибки устанавливаем базовые значения
            data["current_user"] = None
            data["roles"] = {Role.GUEST.value}  # Конвертируем в строку
            return await handler(event, data)

    async def _load_user_with_roles(self, user_id: int, db) -> UsersModel | None:
        """
        Загружает пользователя с ролями из кэша или БД
        
        Args:
            user_id: ID пользователя
            db: Объект базы данных
            
        Returns:
            Модель пользователя с ролями или None
        """
        cache_key = f"rbac:{user_id}"
        user = None
        
        # Пытаемся получить из кэша
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    user_data = json.loads(cached_data)
                    # Восстанавливаем объект пользователя из кэша
                    user = UsersModel(**user_data)
                    logger.debug(f"User {user_id} loaded from cache")
            except Exception as e:
                logger.warning(f"Failed to load user {user_id} from cache: {e}")
        
        # Если не нашли в кэше, загружаем из БД
        if not user:
            user = await db.users.get_user_record(user_id=user_id)
            
            # Сохраняем в кэш
            if user and self.redis:
                try:
                    # Сериализуем пользователя для кэша
                    user_dict = {
                        "user_id": user.user_id,
                        "created": user.created.isoformat(),
                        "language": user.language,
                        "is_alive": user.is_alive,
                        "is_blocked": user.is_blocked,
                        "submission_status": user.submission_status,
                        "task_1_submitted": user.task_1_submitted,
                        "task_2_submitted": user.task_2_submitted,
                        "task_3_submitted": user.task_3_submitted,
                        "roles": user.roles,
                    }
                    await self.redis.setex(
                        cache_key, 
                        self.cache_ttl, 
                        json.dumps(user_dict, default=str)
                    )
                    logger.debug(f"User {user_id} cached for {self.cache_ttl}s")
                except Exception as e:
                    logger.warning(f"Failed to cache user {user_id}: {e}")
        
        return user

    async def _handle_banned_user(self, event: TelegramObject):
        """
        Обрабатывает заблокированного пользователя
        
        Args:
            event: Telegram событие
        """
        # Если это сообщение, отвечаем о блокировке
        if isinstance(event, Message):
            try:
                await event.answer("⛔ Доступ запрещён.")
            except Exception as e:
                logger.warning(f"Failed to send ban message: {e}")
        
        # Логируем попытку доступа заблокированного пользователя
        user = get_event_user(event)
        if user:
            logger.warning(
                f"Banned user {user.id} (@{user.username}) tried to access bot"
            )

    async def invalidate_user_cache(self, user_id: int):
        """
        Инвалидирует кэш пользователя (полезно при изменении ролей)
        
        Args:
            user_id: ID пользователя
        """
        if self.redis:
            try:
                cache_key = f"rbac:{user_id}"
                await self.redis.delete(cache_key)
                logger.debug(f"Cache invalidated for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache for user {user_id}: {e}")