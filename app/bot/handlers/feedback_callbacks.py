"""
Callback handlers for feedback system and main menu navigation
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from app.bot.states.feedback import FeedbackSG
from app.bot.states.main_menu import MainMenuSG
from app.bot.states.interview import InterviewSG
from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.staff.states import StaffMenuSG
from app.bot.dialogs.selections.creative.states import CreativeSelectionSG

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


@feedback_callbacks_router.callback_query(F.data == "go_to_main_menu")
async def go_to_main_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle main menu navigation from inline button"""
    await callback.answer()
    
    # Start main menu dialog
    await dialog_manager.start(
        MainMenuSG.main_menu,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "reschedule_interview")
async def reschedule_interview(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle interview rescheduling from inline button"""
    await callback.answer()
    
    # Start interview dialog to select new time
    await dialog_manager.start(
        InterviewSG.main_menu,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_staff_menu")
async def start_staff_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle staff menu start from inline button (for approved users)"""
    await callback.answer()
    
    # Start main menu dialog for staff
    await dialog_manager.start(
        StaffMenuSG.MAIN,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_guest_menu")
async def start_guest_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle guest menu start from inline button (for declined users)"""
    await callback.answer()
    
    # Start guest menu dialog
    await dialog_manager.start(
        GuestMenuSG.MAIN,
        mode=StartMode.RESET_STACK
    )


@feedback_callbacks_router.callback_query(F.data == "start_creative_selection")
async def start_creative_selection(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle creative selection (casting) start from inline button"""
    await callback.answer()
    
    # Start creative selection dialog
    await dialog_manager.start(
        CreativeSelectionSG.MAIN,
        mode=StartMode.RESET_STACK
    )
