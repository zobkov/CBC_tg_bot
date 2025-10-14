"""
Обработчики для диалога сотрудников
"""
from aiogram_dialog import DialogManager

from .states import StaffMenuSG


async def on_support_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Поддержка"""
    await dialog_manager.switch_to(StaffMenuSG.SUPPORT)


async def on_applications_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Анкеты"""
    await dialog_manager.switch_to(StaffMenuSG.APPLICATIONS)


async def on_back_to_main(callback, widget, dialog_manager: DialogManager):
    """Возврат в главное меню"""
    await dialog_manager.switch_to(StaffMenuSG.MAIN)