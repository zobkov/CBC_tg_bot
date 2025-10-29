"""
Фильтры для исключения legacy интентов из RBAC проверок
"""
import logging
from typing import Dict, Any
from aiogram.filters import Filter
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


class NotLegacyIntent(Filter):
    """
    Фильтр, который пропускает только НЕ legacy интенты.
    Используется для исключения legacy интентов от RBAC проверок.
    
    Legacy интенты обрабатываются напрямую через aiogram-dialog
    без необходимости RBAC проверок, так как у них свой валидатор доступа.
    """

    async def __call__(self, event, **data: Dict[str, Any]) -> bool:
        """
        Проверяет, является ли событие legacy интентом
        
        Args:
            event: Telegram событие (Message или CallbackQuery)
            **data: Данные контекста
            
        Returns:
            True если это НЕ legacy интент (должен пройти через RBAC)
            False если это legacy интент (должен быть исключен из RBAC)
        """
        # Проверяем callback queries на предмет legacy интентов
        if isinstance(event, CallbackQuery) and event.data:
            # Legacy интенты обычно имеют короткие случайные идентификаторы
            # и содержат callback data от старых диалогов
            callback_data = event.data
            
            # Исключаем callback'и с legacy интентами (короткие случайные строки)
            if len(callback_data) <= 10 and not callback_data.startswith('/'):
                # Это может быть legacy intent
                logger.debug(f"Detected potential legacy intent callback: {callback_data}")
                return False
                
            # Исключаем известные legacy callback patterns
            legacy_patterns = [
                'interview_button',
                'current_stage_button', 
                'support_button',
                'apply_button'
            ]
            
            for pattern in legacy_patterns:
                if pattern in callback_data:
                    logger.debug(f"Detected legacy callback pattern: {callback_data}")
                    return False
        
        # Если это обычное сообщение или современный callback - пропускаем через RBAC
        return True


def create_rbac_filter_with_legacy_exclusion(*roles):
    """
    Создает комбинированный фильтр, который проверяет роли только для не-legacy событий
    
    Args:
        *roles: Роли, которые должны быть у пользователя
        
    Returns:
        Фильтр, который проверяет роли, но исключает legacy интенты
    """
    from app.bot.filters.rbac import HasRole
    
    class CombinedFilter(Filter):
        def __init__(self):
            self.rbac_filter = HasRole(*roles)
            self.legacy_filter = NotLegacyIntent()
        
        async def __call__(self, event, **data):
            # Если это legacy интент - разрешаем без RBAC проверки
            if not await self.legacy_filter(event, **data):
                logger.debug("Legacy intent detected, bypassing RBAC filter")
                return True
            
            # Иначе проверяем RBAC
            return await self.rbac_filter(event, **data)
    
    return CombinedFilter()