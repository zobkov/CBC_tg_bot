"""
Handlers for interview dialog - business logic
"""
from datetime import date
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.infrastructure.database.dao.interview import InterviewDAO
from app.bot.states.interview import InterviewSG


async def on_date_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    item_id: str,
    **kwargs
):
    """Handle date selection"""
    await callback.answer()
    
    # Store selected date in dialog data
    manager.dialog_data["selected_date"] = item_id
    
    # Switch to time selection state
    await manager.switch_to(InterviewSG.time_selection)


async def on_timeslot_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    item_id: str,
    **kwargs
):
    """Handle timeslot selection"""
    await callback.answer()
    
    # Store selected timeslot ID in dialog data
    manager.dialog_data["selected_timeslot_id"] = item_id
    
    # Switch to confirmation state
    await manager.switch_to(InterviewSG.confirmation)


async def on_confirm_booking(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle booking confirmation"""
    await callback.answer()
    
    user_id = callback.from_user.id
    timeslot_id = manager.dialog_data.get("selected_timeslot_id")
    
    if not timeslot_id:
        await callback.message.answer("❌ Ошибка: не выбран временной слот")
        return
    
    dao = InterviewDAO(manager.middleware_data["db_applications"])
    
    try:
        success = await dao.book_timeslot(user_id, int(timeslot_id))
        
        if success:
            # Clear dialog data
            manager.dialog_data.clear()
            await manager.switch_to(InterviewSG.success)
        else:
            await callback.message.answer(
                "❌ К сожалению, выбранный временной слот уже занят. "
                "Пожалуйста, выберите другое время."
            )
            # Go back to date selection
            await manager.switch_to(InterviewSG.date_selection)
            
    except Exception as e:
        await callback.message.answer("❌ Произошла ошибка при бронировании. Попробуйте ещё раз.")
        # Log the error
        print(f"Error booking timeslot: {e}")


async def on_cancel_booking(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle booking cancellation (go back to date selection)"""
    await callback.answer()
    
    # Clear selected timeslot
    manager.dialog_data.pop("selected_timeslot_id", None)
    
    # Go back to time selection
    await manager.switch_to(InterviewSG.time_selection)


async def on_back_to_dates(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle going back to date selection"""
    await callback.answer()
    
    # Clear selected date and timeslot
    manager.dialog_data.pop("selected_date", None)
    manager.dialog_data.pop("selected_timeslot_id", None)
    
    await manager.switch_to(InterviewSG.date_selection)


async def on_reschedule_request(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle reschedule request"""
    await callback.answer()
    
    await manager.switch_to(InterviewSG.reschedule_date_selection)


async def on_reschedule_date_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    item_id: str,
    **kwargs
):
    """Handle date selection in reschedule flow"""
    await callback.answer()
    
    # Store selected date in dialog data
    manager.dialog_data["reschedule_date"] = item_id
    
    # Switch to reschedule time selection state
    await manager.switch_to(InterviewSG.reschedule_time_selection)


async def on_reschedule_timeslot_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    item_id: str,
    **kwargs
):
    """Handle timeslot selection in reschedule flow"""
    await callback.answer()
    
    # Store selected timeslot ID in dialog data
    manager.dialog_data["reschedule_timeslot_id"] = item_id
    
    # Switch to reschedule confirmation state
    await manager.switch_to(InterviewSG.reschedule_confirmation)


async def on_confirm_reschedule(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle reschedule confirmation"""
    await callback.answer()
    
    user_id = callback.from_user.id
    new_timeslot_id = manager.dialog_data.get("reschedule_timeslot_id")
    
    if not new_timeslot_id:
        await callback.message.answer("❌ Ошибка: не выбран новый временной слот")
        return
    
    dao = InterviewDAO(manager.middleware_data["db_applications"])
    
    try:
        success = await dao.book_timeslot(user_id, int(new_timeslot_id))
        
        if success:
            # Clear dialog data
            manager.dialog_data.clear()
            await callback.message.answer(
                "✅ Интервью успешно перенесено! "
                "Информация о новом времени отправлена менеджеру."
            )
            await manager.switch_to(InterviewSG.main_menu)
        else:
            await callback.message.answer(
                "❌ К сожалению, выбранный временной слот уже занят. "
                "Пожалуйста, выберите другое время."
            )
            # Go back to reschedule date selection
            await manager.switch_to(InterviewSG.reschedule_date_selection)
            
    except Exception as e:
        await callback.message.answer("❌ Произошла ошибка при переносе. Попробуйте ещё раз.")
        # Log the error
        print(f"Error rescheduling timeslot: {e}")


async def on_cancel_reschedule(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle reschedule cancellation"""
    await callback.answer()
    
    # Clear reschedule data
    manager.dialog_data.pop("reschedule_date", None)
    manager.dialog_data.pop("reschedule_timeslot_id", None)
    
    # Go back to main menu
    await manager.switch_to(InterviewSG.main_menu)