"""
Handlers for feedback dialog - business logic
"""
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.infrastructure.database.dao.feedback import FeedbackDAO
from app.bot.states.feedback import FeedbackSG
from app.bot.states.main_menu import MainMenuSG


async def on_feedback_position_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    item_id: str,
    **kwargs
):
    """Handle feedback position selection"""
    await callback.answer()
    
    # Parse item_id to get priority
    try:
        # Extract priority from item_id like "fb_pos_1" -> 1
        priority = int(item_id.replace("fb_pos_", ""))
        
        # Get position info for the selected priority
        dao = FeedbackDAO(manager.middleware_data["db_applications"], manager.middleware_data["config"])
        user_id = callback.from_user.id
        
        feedback_positions = await dao.get_user_feedback_positions(user_id)
        selected_position = None
        
        for pos in feedback_positions:
            if pos["priority"] == priority:
                selected_position = pos
                break
        
        if selected_position:
            # Store selected position in dialog data
            manager.dialog_data["selected_position"] = selected_position
            
            # Switch to feedback display state
            await manager.switch_to(FeedbackSG.show_feedback)
        else:
            await callback.message.answer("❌ Обратная связь не найдена")
            
    except (ValueError, Exception) as e:
        print(f"Error selecting feedback position: {e}")
        await callback.message.answer("❌ Произошла ошибка")


async def on_back_to_feedback_menu(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle going back to feedback menu"""
    await callback.answer()
    
    # Clear selected position
    manager.dialog_data.pop("selected_position", None)
    
    await manager.switch_to(FeedbackSG.feedback_menu)


async def on_back_to_main_menu(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    **kwargs
):
    """Handle going back to main menu"""
    await callback.answer()
    
    # Clear dialog data
    manager.dialog_data.clear()
    
    # Go to main menu
    await manager.start(MainMenuSG.main_menu)