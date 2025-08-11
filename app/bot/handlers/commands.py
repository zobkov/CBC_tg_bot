from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter

from aiogram_dialog import DialogManager, StartMode

from app.bot.states.start import StartSG
from app.bot.states.main_menu import MainMenuSG

router = Router()


@router.message(CommandStart())
async def process_command_start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)

@router.message(Command(commands=['menu']))
async def process_command_menu(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=MainMenuSG.main_menu, mode=StartMode.RESET_STACK)