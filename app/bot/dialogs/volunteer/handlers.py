"""
Обработчики для диалога волонтёров
"""
from aiogram_dialog import DialogManager

from .states import VolunteerMenuSG


async def on_support_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Поддержка"""
    await dialog_manager.switch_to(VolunteerMenuSG.SUPPORT)


async def on_help_users_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Помощь пользователям"""
    await dialog_manager.switch_to(VolunteerMenuSG.HELP_USERS)


async def on_back_to_main(callback, widget, dialog_manager: DialogManager):
    """Возврат в главное меню"""
    await dialog_manager.switch_to(VolunteerMenuSG.MAIN)