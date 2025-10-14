"""
Getters for interview dialog - data retrieval functions
"""
from datetime import date, time
from typing import Dict, Any, List

from aiogram_dialog import DialogManager

from app.infrastructure.database.dao.interview import InterviewDAO


async def get_user_approved_department(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get the department number and position info for which user was approved"""
    user_id = dialog_manager.event.from_user.id
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    
    # Get basic department number for interview scheduling
    approved_dept = await dao.get_user_approved_department(user_id)
    
    # Get full position information for display
    position_info = await dao.get_user_approved_position_info(user_id)
    
    if position_info:
        return {
            "approved_department": approved_dept,
            "has_approval": approved_dept > 0,
            "approved_position_title": position_info["full_title"],
            "department_name": position_info["department_name"],
            "subdepartment_name": position_info["subdepartment_name"],
            "position_name": position_info["position_name"]
        }
    else:
        return {
            "approved_department": approved_dept,
            "has_approval": approved_dept > 0,
            "approved_position_title": f"Отдел {approved_dept}" if approved_dept > 0 else "",
            "department_name": "",
            "subdepartment_name": "",
            "position_name": ""
        }


async def get_available_dates(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get available interview dates for user's approved department"""
    user_id = dialog_manager.event.from_user.id
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    
    approved_dept = await dao.get_user_approved_department(user_id)
    if approved_dept == 0:
        return {"dates": [], "department_number": 0}
    
    available_dates = await dao.get_available_dates_for_department(approved_dept)
    
    # Format dates for display
    formatted_dates = []
    for date_obj in available_dates:
        formatted_dates.append({
            "date": date_obj,
            "display": date_obj.strftime("%d октября"),
            "value": date_obj.isoformat()
        })
    
    return {
        "dates": formatted_dates,
        "department_number": approved_dept
    }


async def get_available_timeslots(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get available time slots for selected date"""
    user_id = dialog_manager.event.from_user.id
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    
    # Get selected date from dialog data
    selected_date_str = dialog_manager.dialog_data.get("selected_date")
    if not selected_date_str:
        return {"timeslots": [], "selected_date_display": ""}
    
    selected_date = date.fromisoformat(selected_date_str)
    approved_dept = await dao.get_user_approved_department(user_id)
    
    if approved_dept == 0:
        return {"timeslots": [], "selected_date_display": ""}
    
    timeslots = await dao.get_available_timeslots_for_date(approved_dept, selected_date)
    
    # Format timeslots for display in two columns
    formatted_timeslots = []
    for slot in timeslots:
        formatted_timeslots.append({
            "id": slot["id"],
            "time": slot["start_time"],
            "display": slot["start_time"].strftime("%H:%M"),
            "value": str(slot["id"])
        })
    
    return {
        "timeslots": formatted_timeslots,
        "selected_date_display": selected_date.strftime("%d октября"),
        "total_slots": len(formatted_timeslots)
    }


async def get_current_booking(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get user's current interview booking if any"""
    user_id = dialog_manager.event.from_user.id
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    
    booking = await dao.get_user_current_booking(user_id)
    
    if booking:
        return {
            "has_booking": True,
            "booking_date": booking["interview_date"].strftime("%d октября"),
            "booking_time": booking["start_time"].strftime("%H:%M"),
            "booking_id": booking["id"]
        }
    
    return {"has_booking": False}


async def get_selected_timeslot_info(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get information about selected timeslot for confirmation"""
    selected_timeslot_id = dialog_manager.dialog_data.get("selected_timeslot_id")
    if not selected_timeslot_id:
        return {"timeslot_info": None}
    
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    timeslot = await dao.get_timeslot_by_id(int(selected_timeslot_id))
    
    if timeslot:
        return {
            "timeslot_info": {
                "date": timeslot["interview_date"].strftime("%d октября"),
                "time": timeslot["start_time"].strftime("%H:%M"),
                "id": timeslot["id"]
            }
        }
    
    return {"timeslot_info": None}


async def get_reschedule_timeslots(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get available time slots for reschedule date"""
    user_id = dialog_manager.event.from_user.id
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    
    # Get selected date from dialog data (reschedule flow)
    selected_date_str = dialog_manager.dialog_data.get("reschedule_date")
    if not selected_date_str:
        return {"timeslots": [], "selected_date_display": ""}
    
    selected_date = date.fromisoformat(selected_date_str)
    approved_dept = await dao.get_user_approved_department(user_id)
    
    if approved_dept == 0:
        return {"timeslots": [], "selected_date_display": ""}
    
    timeslots = await dao.get_available_timeslots_for_date(approved_dept, selected_date)
    
    # Format timeslots for display in two columns
    formatted_timeslots = []
    for slot in timeslots:
        formatted_timeslots.append({
            "id": slot["id"],
            "time": slot["start_time"],
            "display": slot["start_time"].strftime("%H:%M"),
            "value": str(slot["id"])
        })
    
    return {
        "timeslots": formatted_timeslots,
        "selected_date_display": selected_date.strftime("%d октября"),
        "total_slots": len(formatted_timeslots)
    }


async def get_reschedule_timeslot_info(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Get information about selected reschedule timeslot for confirmation"""
    selected_timeslot_id = dialog_manager.dialog_data.get("reschedule_timeslot_id")
    if not selected_timeslot_id:
        return {"timeslot_info": None}
    
    dao = InterviewDAO(dialog_manager.middleware_data["db_applications"], dialog_manager.middleware_data["config"])
    timeslot = await dao.get_timeslot_by_id(int(selected_timeslot_id))
    
    if timeslot:
        return {
            "timeslot_info": {
                "date": timeslot["interview_date"].strftime("%d октября"),
                "time": timeslot["start_time"].strftime("%H:%M"),
                "id": timeslot["id"]
            }
        }
    
    return {"timeslot_info": None}