"""
Getters for feedback dialog - data retrieval functions
"""
from typing import Dict, Any, List
from aiogram_dialog import DialogManager

from app.infrastructure.database.dao.feedback import FeedbackDAO


async def get_user_feedback_positions(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get positions with available feedback for user"""
    dao = FeedbackDAO(dialog_manager.middleware_data["db_applications"])
    user_id = dialog_manager.event.from_user.id
    
    # Get user's applications with feedback
    feedback_positions = await dao.get_user_feedback_positions(user_id)
    
    return {
        "feedback_positions": feedback_positions,
        "has_feedback": len(feedback_positions) > 0
    }


async def get_selected_feedback(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get specific feedback content"""
    dao = FeedbackDAO(dialog_manager.middleware_data["db_applications"])
    user_id = dialog_manager.event.from_user.id
    
    # Get position info from dialog data
    position_info = dialog_manager.dialog_data.get("selected_position")
    
    if not position_info:
        return {"feedback_text": "Обратная связь не найдена.", "position_info": {}}
    
    feedback_data = await dao.get_feedback_for_position(
        user_id, 
        position_info["priority"]
    )
    
    return {
        "feedback_text": feedback_data.get("feedback", "Обратная связь отсутствует."),
        "position_info": position_info
    }