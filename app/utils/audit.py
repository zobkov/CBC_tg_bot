"""
Система аудита и мониторинга попыток несанкционированного доступа
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.utils.telegram import get_user_id_from_event, get_username_from_event

logger = logging.getLogger("rbac.audit")


class RBACAuthAuditor:
    """
    Система аудита и мониторинга попыток несанкционированного доступа.
    
    Функции:
    - Логирование попыток доступа
    - Обнаружение флуда (rate limiting)
    - Алерты для администраторов
    - Автоматическая блокировка при превышении лимитов
    """

    def __init__(self, redis=None, alert_chat_id: Optional[int] = None):
        """
        Args:
            redis: Redis клиент для хранения счетчиков
            alert_chat_id: ID чата для отправки алертов администраторам
        """
        self.redis = redis
        self.alert_chat_id = alert_chat_id
        
        # Настройки лимитов
        self.forbidden_limit = 5  # Максимум попыток за окно
        self.window_seconds = 60  # Окно времени в секундах
        self.ban_threshold = 10   # При превышении - временная блокировка
        self.ban_duration = 300   # Длительность блокировки (5 минут)

    async def audit_forbidden_access(
        self, 
        event, 
        handler_name: str = "unknown", 
        reason: str = "access_denied"
    ):
        """
        Регистрирует попытку несанкционированного доступа
        
        Args:
            event: Telegram событие
            handler_name: Название обработчика/команды
            reason: Причина отказа в доступе
        """
        user_id = get_user_id_from_event(event)
        if not user_id:
            return
        
        username = get_username_from_event(event)
        
        # Логируем событие
        logger.warning(
            "RBAC 403: user_id=%s username=%s handler=%s reason=%s",
            user_id, username or "no_username", handler_name, reason
        )
        
        # Увеличиваем счетчик попыток
        if self.redis:
            await self._increment_attempt_counter(user_id)
        
        # Проверяем на флуд
        await self._check_flood_protection(user_id, username, handler_name)

    async def _increment_attempt_counter(self, user_id: int) -> int:
        """
        Увеличивает счетчик попыток несанкционированного доступа
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Текущее количество попыток в окне
        """
        key = f"audit:403:{user_id}"
        
        try:
            # Увеличиваем счетчик
            count = await self.redis.incr(key)
            
            # Устанавливаем TTL при первой попытке
            if count == 1:
                await self.redis.expire(key, self.window_seconds)
            
            return count
        except Exception as e:
            logger.error(f"Error incrementing attempt counter: {e}")
            return 0

    async def _check_flood_protection(
        self, 
        user_id: int, 
        username: Optional[str], 
        handler_name: str
    ):
        """
        Проверяет превышение лимитов и принимает меры
        
        Args:
            user_id: ID пользователя
            username: Username пользователя
            handler_name: Название обработчика
        """
        if not self.redis:
            return
        
        try:
            key = f"audit:403:{user_id}"
            count = await self.redis.get(key)
            
            if not count:
                return
            
            count = int(count)
            
            # Проверяем лимиты
            if count >= self.ban_threshold:
                await self._handle_ban_threshold(user_id, username, count)
            elif count >= self.forbidden_limit:
                await self._handle_flood_alert(user_id, username, count, handler_name)
                
        except Exception as e:
            logger.error(f"Error in flood protection check: {e}")

    async def _handle_flood_alert(
        self, 
        user_id: int, 
        username: Optional[str], 
        count: int, 
        handler_name: str
    ):
        """
        Отправляет алерт о превышении лимита попыток доступа
        
        Args:
            user_id: ID пользователя
            username: Username пользователя  
            count: Количество попыток
            handler_name: Название обработчика
        """
        alert_message = (
            f"⚠️ <b>RBAC Security Alert</b>\n\n"
            f"👤 User: {user_id} (@{username or 'no_username'})\n"
            f"🔢 Attempts: {count}/{self.window_seconds}s\n"
            f"🎯 Handler: {handler_name}\n"
            f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"Пользователь превысил лимит попыток несанкционированного доступа."
        )
        
        logger.error(
            f"FLOOD ALERT: user {user_id} ({count} attempts in {self.window_seconds}s)"
        )
        
        # TODO: Отправить алерт в админ-чат если настроен
        if self.alert_chat_id:
            # await bot.send_message(self.alert_chat_id, alert_message)
            pass

    async def _handle_ban_threshold(
        self, 
        user_id: int, 
        username: Optional[str], 
        count: int
    ):
        """
        Обрабатывает превышение порога для временной блокировки
        
        Args:
            user_id: ID пользователя
            username: Username пользователя
            count: Количество попыток
        """
        # Устанавливаем временную блокировку
        ban_key = f"audit:tempban:{user_id}"
        
        try:
            await self.redis.setex(ban_key, self.ban_duration, "1")
            
            ban_alert = (
                f"🚨 <b>RBAC Temporary Ban</b>\n\n"
                f"👤 User: {user_id} (@{username or 'no_username'})\n"
                f"🔢 Attempts: {count}\n"
                f"⏱ Ban Duration: {self.ban_duration // 60} minutes\n"
                f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"Пользователь временно заблокирован за превышение лимита попыток."
            )
            
            logger.critical(
                f"TEMPORARY BAN: user {user_id} banned for {self.ban_duration}s "
                f"due to {count} unauthorized access attempts"
            )
            
            # TODO: Отправить критический алерт в админ-чат
            if self.alert_chat_id:
                # await bot.send_message(self.alert_chat_id, ban_alert)
                pass
                
        except Exception as e:
            logger.error(f"Error setting temporary ban: {e}")

    async def is_temporarily_banned(self, user_id: int) -> bool:
        """
        Проверяет, находится ли пользователь во временной блокировке
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если пользователь временно заблокирован
        """
        if not self.redis:
            return False
        
        try:
            ban_key = f"audit:tempban:{user_id}"
            return bool(await self.redis.get(ban_key))
        except Exception as e:
            logger.error(f"Error checking temporary ban: {e}")
            return False

    async def get_user_attempt_stats(self, user_id: int) -> dict:
        """
        Получает статистику попыток пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь со статистикой
        """
        if not self.redis:
            return {"attempts": 0, "banned": False}
        
        try:
            attempt_key = f"audit:403:{user_id}"
            ban_key = f"audit:tempban:{user_id}"
            
            attempts = await self.redis.get(attempt_key)
            banned = await self.redis.get(ban_key)
            
            return {
                "attempts": int(attempts) if attempts else 0,
                "banned": bool(banned),
                "limit": self.forbidden_limit,
                "window": self.window_seconds
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"attempts": 0, "banned": False}

    async def clear_user_violations(self, user_id: int):
        """
        Очищает нарушения пользователя (для админов)
        
        Args:
            user_id: ID пользователя
        """
        if not self.redis:
            return
        
        try:
            attempt_key = f"audit:403:{user_id}"
            ban_key = f"audit:tempban:{user_id}"
            
            await self.redis.delete(attempt_key, ban_key)
            
            logger.info(f"Cleared violations for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing violations: {e}")


# Глобальный экземпляр аудитора
_auditor: Optional[RBACAuthAuditor] = None


def init_auditor(redis=None, alert_chat_id: Optional[int] = None):
    """
    Инициализирует глобальный аудитор
    
    Args:
        redis: Redis клиент
        alert_chat_id: ID чата для алертов
    """
    global _auditor
    _auditor = RBACAuthAuditor(redis=redis, alert_chat_id=alert_chat_id)


def get_auditor() -> Optional[RBACAuthAuditor]:
    """Получает глобальный аудитор"""
    return _auditor


async def audit_forbidden(
    event, 
    handler_name: str = "unknown", 
    reason: str = "access_denied"
):
    """
    Удобная функция для аудита попыток несанкционированного доступа
    
    Args:
        event: Telegram событие
        handler_name: Название обработчика
        reason: Причина отказа
    """
    if _auditor:
        await _auditor.audit_forbidden_access(event, handler_name, reason)