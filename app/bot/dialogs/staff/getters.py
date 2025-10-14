"""
Getters для диалога сотрудников - функции получения данных
"""
from typing import Dict, Any
from aiogram_dialog import DialogManager


async def get_staff_menu_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для главного меню сотрудника"""
    # Здесь можно добавить логику получения данных из БД
    # Например, количество новых заявок, уведомления и т.д.
    
    # Получаем имя из Telegram API через event
    user_name = "Сотрудник"
    if hasattr(dialog_manager, 'event') and hasattr(dialog_manager.event, 'from_user'):
        user_name = dialog_manager.event.from_user.first_name or "Сотрудник"
    
    return {
        "user_name": user_name,
        # В будущем можно добавить:
        # "pending_applications": await get_pending_applications_count(),
        # "notifications": await get_staff_notifications(),
    }


async def get_applications_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для раздела анкет"""
    return {
        "status": "В разработке",
        # В будущем:
        # "applications_count": await get_applications_count(),
        # "pending_review": await get_pending_review_count(),
    }


async def get_support_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для раздела поддержки"""
    return {
        "support_contacts": {
            "tech_support": "@tech_support",
            "coordinators": "@cbc_coordinators", 
            "developers": "@dev_team"
        }
    }