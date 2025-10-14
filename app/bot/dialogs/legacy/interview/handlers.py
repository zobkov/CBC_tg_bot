"""
Handlers for interview dialog - business logic
"""
import asyncio
from datetime import date
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from app.infrastructure.database.dao.interview import InterviewDAO
from app.services.interview_google_sync import InterviewGoogleSheetsSync
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
    
    user_id = callback.from_user.id
    dao = InterviewDAO(manager.middleware_data["db_applications"], manager.middleware_data["config"])
    
    try:
        # Проверяем актуальную информацию о слоте
        timeslot_info = await dao.get_timeslot_by_id(int(item_id))
        
        if not timeslot_info:
            # Слот не найден
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Timeslot {item_id} not found for user {user_id}")
            
            await callback.message.answer(
                "❌ К сожалению, кто-то уже занял это время. Выбери, пожалуйста, другое."
            )
            await manager.switch_to(InterviewSG.date_selection)
            return
        
        # Проверяем, доступен ли слот и не занят ли он
        if not timeslot_info.get("is_available") or timeslot_info.get("reserved_by") is not None:
            # Слот уже занят
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Race condition detected: user {user_id} tried to select already occupied timeslot {item_id}. "
                f"Slot info: is_available={timeslot_info.get('is_available')}, "
                f"reserved_by={timeslot_info.get('reserved_by')}"
            )
            
            await callback.message.answer(
                "❌ К сожалению, кто-то уже занял это время. Выбери, пожалуйста, другое."
            )
            await manager.switch_to(InterviewSG.date_selection)
            return
        
        # Слот доступен, сохраняем выбор
        manager.dialog_data["selected_timeslot_id"] = item_id
        
        # Переходим к подтверждению
        await manager.switch_to(InterviewSG.confirmation)
        
    except Exception as e:
        # Ошибка при проверке слота
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking timeslot {item_id} for user {user_id}: {e}")
        
        await callback.message.answer(
            "❌ Произошла ошибка при выборе времени. Попробуйте ещё раз."
        )
        await manager.switch_to(InterviewSG.date_selection)


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
    
    dao = InterviewDAO(manager.middleware_data["db_applications"], manager.middleware_data["config"])
    
    try:
        # Get timeslot info before booking
        timeslot_info = await dao.get_timeslot_by_id(int(timeslot_id))
        if not timeslot_info:
            await callback.message.answer("❌ Ошибка: временной слот не найден")
            return
        
        success = await dao.book_timeslot(user_id, int(timeslot_id))
        
        if success:
            # Sync with Google Sheets in background
            try:
                sync_service = InterviewGoogleSheetsSync(dao)
                asyncio.create_task(sync_service.sync_single_timeslot_change(
                    department_number=timeslot_info["department_number"],
                    slot_date=timeslot_info["interview_date"],
                    slot_time=timeslot_info["start_time"],
                    user_id=user_id
                ))
            except Exception as e:
                print(f"Warning: Google Sheets sync failed: {e}")
            
            # Clear dialog data
            manager.dialog_data.clear()
            await manager.switch_to(InterviewSG.success)
        else:
            await callback.message.answer(
                "❌ К сожалению, выбранный временной слот уже занят. "
                "Пожалуйста, выбери другое время 🫶"
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
    
    user_id = callback.from_user.id
    dao = InterviewDAO(manager.middleware_data["db_applications"], manager.middleware_data["config"])
    
    try:
        # Проверяем актуальную информацию о слоте
        timeslot_info = await dao.get_timeslot_by_id(int(item_id))
        
        if not timeslot_info:
            # Слот не найден
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Reschedule: Timeslot {item_id} not found for user {user_id}")
            
            await callback.message.answer(
                "❌ К сожалению, кто-то уже занял это время. Выбери, пожалуйста, другое."
            )
            await manager.switch_to(InterviewSG.reschedule_date_selection)
            return
        
        # Проверяем, доступен ли слот и не занят ли он
        if not timeslot_info.get("is_available") or timeslot_info.get("reserved_by") is not None:
            # Слот уже занят
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Reschedule race condition detected: user {user_id} tried to select already occupied timeslot {item_id}. "
                f"Slot info: is_available={timeslot_info.get('is_available')}, "
                f"reserved_by={timeslot_info.get('reserved_by')}"
            )
            
            await callback.message.answer(
                "❌ К сожалению, кто-то уже занял это время. Выбери, пожалуйста, другое."
            )
            await manager.switch_to(InterviewSG.reschedule_date_selection)
            return
        
        # Слот доступен, сохраняем выбор
        manager.dialog_data["reschedule_timeslot_id"] = item_id
        
        # Переходим к подтверждению переноса
        await manager.switch_to(InterviewSG.reschedule_confirmation)
        
    except Exception as e:
        # Ошибка при проверке слота
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking reschedule timeslot {item_id} for user {user_id}: {e}")
        
        await callback.message.answer(
            "❌ Произошла ошибка при выборе времени. Попробуйте ещё раз."
        )
        await manager.switch_to(InterviewSG.reschedule_date_selection)


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
    
    dao = InterviewDAO(manager.middleware_data["db_applications"], manager.middleware_data["config"])
    
    try:
        # Get old booking info before rescheduling for sync
        old_booking = await dao.get_user_current_booking(user_id)
        
        # Get new timeslot info before booking
        new_timeslot_info = await dao.get_timeslot_by_id(int(new_timeslot_id))
        if not new_timeslot_info:
            await callback.message.answer("❌ Ошибка: новый временной слот не найден")
            return
        
        success = await dao.book_timeslot(user_id, int(new_timeslot_id))
        
        if success:
            # Sync with Google Sheets in background
            try:
                sync_service = InterviewGoogleSheetsSync(dao)
                
                # Sync old booking removal (if exists)
                if old_booking:
                    asyncio.create_task(sync_service.sync_single_timeslot_change(
                        department_number=old_booking["department_number"],
                        slot_date=old_booking["interview_date"],
                        slot_time=old_booking["start_time"],
                        user_id=None  # None means remove booking
                    ))
                
                # Sync new booking
                asyncio.create_task(sync_service.sync_single_timeslot_change(
                    department_number=new_timeslot_info["department_number"],
                    slot_date=new_timeslot_info["interview_date"],
                    slot_time=new_timeslot_info["start_time"],
                    user_id=user_id
                ))
            except Exception as e:
                print(f"Warning: Google Sheets sync failed during reschedule: {e}")
            
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
                "Пожалуйста, выбери другое время 🫶."
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


async def on_cancel_interview_request(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle cancel interview request"""
    await callback.answer()
    
    await manager.switch_to(InterviewSG.cancel_confirmation)


async def on_confirm_cancel_interview(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle cancel interview confirmation"""
    await callback.answer()
    
    user_id = callback.from_user.id
    dao = InterviewDAO(manager.middleware_data["db_applications"], manager.middleware_data["config"])
    
    try:
        # Get current booking info before cancellation for sync
        current_booking = await dao.get_user_current_booking(user_id)
        
        success = await dao.cancel_user_booking(user_id)
        
        if success:
            # Sync with Google Sheets in background
            try:
                sync_service = InterviewGoogleSheetsSync(dao)
                
                # Sync booking removal (if booking exists)
                if current_booking:
                    asyncio.create_task(sync_service.sync_single_timeslot_change(
                        department_number=current_booking["department_number"],
                        slot_date=current_booking["interview_date"],
                        slot_time=current_booking["start_time"],
                        user_id=None  # None means remove booking
                    ))
            except Exception as e:
                print(f"Warning: Google Sheets sync failed during cancellation: {e}")
            
            await callback.message.answer(
                "✅ <b>Запись на онлайн-собеседование отменена</b> \n\nНичего страшного — ты можешь выбрать новое время в любой момент, когда будет удобно!"
            )
            await manager.switch_to(InterviewSG.main_menu, show_mode=ShowMode.DELETE_AND_SEND)
        else:
            await callback.message.answer("❌ Произошла ошибка при отмене записи. Попробуйте ещё раз.")
            await manager.switch_to(InterviewSG.main_menu, show_mode=ShowMode.DELETE_AND_SEND)
            
    except Exception as e:
        await callback.message.answer("❌ Произошла ошибка при отмене записи. Попробуйте ещё раз.")
        print(f"Error cancelling interview: {e}")
        await manager.switch_to(InterviewSG.main_menu,show_mode=ShowMode.DELETE_AND_SEND)


async def on_cancel_interview_cancellation(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle cancellation of interview cancellation (go back to main menu)"""
    await callback.answer()
    
    # Go back to main menu
    await manager.switch_to(InterviewSG.main_menu)