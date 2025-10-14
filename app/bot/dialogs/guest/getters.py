"""
Getters для диалога гостей - функции получения данных
"""
from typing import Dict, Any
from aiogram_dialog import DialogManager


async def get_guest_menu_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для главного меню гостя"""
    
    # Получаем имя из Telegram API через event
    user_name = "Участник"
    if hasattr(dialog_manager, 'event') and hasattr(dialog_manager.event, 'from_user'):
        user_name = dialog_manager.event.from_user.first_name or "Участник"
    
    return {
        "user_name": user_name,
        # В будущем можно добавить:
        # "application_status": await get_application_status(),
        # "available_tasks": await get_available_tasks(),
    }


async def get_support_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получить данные для раздела поддержки"""
    return {
        "support_email": "support@cbc.example.com",
        "response_time": "в рабочие дни до 24 часов"
    }