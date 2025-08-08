from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, StateFilter

from aiogram_dialog import DialogManager, StartMode

from app.bot.states.start import StartSG

router = Router()


@router.message(CommandStart())
async def process_command_start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)