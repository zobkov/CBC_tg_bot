from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager

from app.bot.states.first_stage import FirstStageSG
from app.bot.states.main_menu import MainMenuSG
from app.bot.states.tasks import TasksSG

async def on_live_task_1_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовое задание 1'"""

    await dialog_manager.switch_to(state=TasksSG.task_1)


async def on_live_task_2_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовое задание 3'"""

    await dialog_manager.switch_to(state=TasksSG.task_2)

async def on_live_task_3_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовое задание 3'"""

    await dialog_manager.switch_to(state=TasksSG.task_3)
