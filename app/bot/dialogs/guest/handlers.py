"""
Обработчики для диалога гостей
"""
from aiogram_dialog import DialogManager

from .states import GuestMenuSG


async def on_support_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Поддержка"""
    await dialog_manager.switch_to(GuestMenuSG.SUPPORT)


async def on_back_to_main(callback, widget, dialog_manager: DialogManager):
    """Возврат в главное меню"""
    await dialog_manager.switch_to(GuestMenuSG.MAIN)