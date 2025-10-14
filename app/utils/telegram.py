"""
Утилиты для работы с Telegram событиями
"""
from aiogram.types import TelegramObject, Message, CallbackQuery, User


def get_event_user(event: TelegramObject) -> User | None:
    """
    Извлекает пользователя из любого Telegram события.
    
    Args:
        event: Любой объект события Telegram (Message, CallbackQuery, etc.)
        
    Returns:
        User объект если найден, иначе None
    """
    # Message
    if isinstance(event, Message) and event.from_user:
        return event.from_user
    
    # CallbackQuery
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user
    
    # Попытка универсального fallback
    from_user = getattr(event, "from_user", None)
    if from_user:
        return from_user
    
    # Проверяем вложенное сообщение (например, в CallbackQuery)
    message = getattr(event, "message", None)
    if message and getattr(message, "from_user", None):
        return message.from_user
    
    return None


def get_user_id_from_event(event: TelegramObject) -> int | None:
    """
    Извлекает ID пользователя из любого Telegram события.
    
    Args:
        event: Любой объект события Telegram
        
    Returns:
        ID пользователя если найден, иначе None
    """
    user = get_event_user(event)
    return user.id if user else None


def get_username_from_event(event: TelegramObject) -> str | None:
    """
    Извлекает username пользователя из любого Telegram события.
    
    Args:
        event: Любой объект события Telegram
        
    Returns:
        Username пользователя если найден, иначе None
    """
    user = get_event_user(event)
    return user.username if user else None


def get_full_name_from_event(event: TelegramObject) -> str | None:
    """
    Извлекает полное имя пользователя из любого Telegram события.
    
    Args:
        event: Любой объект события Telegram
        
    Returns:
        Полное имя пользователя если найдено, иначе None
    """
    user = get_event_user(event)
    if not user:
        return None
    
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    
    return " ".join(parts) if parts else None