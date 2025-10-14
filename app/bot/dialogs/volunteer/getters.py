"""
Getters для диалога волонтёров - функции получения данных
"""
from typing import Dict, Any
from aiogram_dialog import DialogManager


async def get_volunteer_menu_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для главного меню волонтёра"""
    
    # Получаем имя из Telegram API через event
    user_name = "Волонтёр"
    if hasattr(dialog_manager, 'event') and hasattr(dialog_manager.event, 'from_user'):
        user_name = dialog_manager.event.from_user.first_name or "Волонтёр"
    
    return {
        "user_name": user_name,
        # В будущем можно добавить:
        # "pending_requests": await get_pending_support_requests(),
        # "active_users": await get_active_users_count(),
    }


async def get_help_users_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для раздела помощи пользователям"""
    return {
        "tools": {
            "faq": "/faq",
            "instructions": "/instructions", 
            "contacts": "/contacts"
        },
        # В будущем:
        # "pending_requests_count": await get_pending_requests_count(),
        # "active_chats": await get_active_support_chats(),
    }


async def get_support_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для раздела поддержки волонтёров"""
    return {
        "contacts": {
            "volunteer_lead": "@volunteer_lead",
            "cbc_staff": "@cbc_staff",
            "tech_support": "@tech_support"
        }
    }