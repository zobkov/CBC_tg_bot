"""
Callback handlers for feedback system
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from app.bot.states.feedback import FeedbackSG

feedback_callbacks_router = Router()


@feedback_callbacks_router.callback_query(F.data == "start_feedback_dialog")
async def start_feedback_dialog(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle feedback dialog start from inline button"""
    await callback.answer()
    
    # Start feedback dialog
    await dialog_manager.start(
        FeedbackSG.feedback_menu,
        mode=StartMode.RESET_STACK
    )