from typing import Dict, Any

from aiogram.types import User
from aiogram_dialog import DialogManager

from config.config import Config
from app.infrastructure.database.database.db import DB


async def get_stage_info(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о первом этапе"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {
            "stage_title": "Первый этап",
            "stage_description": "Информация недоступна",
            "can_apply": False,
            "application_status": "Ошибка загрузки"
        }
    
    stage_info = config.selection.stages["stage_1"]
    
    # Проверяем статус заявки пользователя
    event_from_user = dialog_manager.event.from_user
    db: DB = dialog_manager.middleware_data.get("db")
    
    can_apply = True
    application_status_text = ""
    
    try:
        if db:
            # TODO: Здесь будет проверка статуса заявки
            pass
    except Exception as e:
        print(f"Ошибка при проверке статуса заявки: {e}")
    
    return {
        "stage_name": stage_info["name"],
        "stage_description": stage_info["description"],
        "can_apply": can_apply,
        "application_status_text": application_status_text
    }


async def get_how_found_options(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем варианты ответов на вопрос 'Откуда узнали о КБК'"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"how_found_options": []}
    
    options = []
    for i, option in enumerate(config.selection.how_found_options):
        options.append({"id": str(i), "text": option})
    
    return {"how_found_options": options}


async def get_departments(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем список департаментов"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"departments": []}
    
    departments = []
    for key, dept_info in config.selection.departments.items():
        departments.append({
            "id": key, 
            "text": dept_info["name"],
            "description": dept_info.get("description", "")
        })
    
    return {"departments": departments}


async def get_positions_for_department(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем должности для выбранного отдела"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"positions": []}
    
    # Получаем выбранный отдел из контекста диалога
    dialog_data = dialog_manager.dialog_data
    selected_department = dialog_data.get("selected_department")
    
    positions = []
    department_name = ""
    
    if selected_department and selected_department in config.selection.departments:
        dept_info = config.selection.departments[selected_department]
        dept_positions = dept_info.get("positions", [])
        department_name = dept_info.get("name", "")
        
        for i, position in enumerate(dept_positions):
            positions.append({"id": str(i), "text": position})
    
    return {
        "positions": positions,
        "department_name": department_name
    }


async def get_course_options(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем варианты курсов"""
    courses = []
    for i in range(1, 7):  # курсы 1-6
        courses.append({"id": str(i), "text": f"{i} курс"})
    
    return {"courses": courses}


async def get_form_summary(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем сводку заполненной формы"""
    dialog_data = dialog_manager.dialog_data
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"summary": "Ошибка загрузки конфигурации"}
    
    # Получаем выбранные варианты
    how_found_idx = dialog_data.get("how_found_kbk", "0")
    try:
        how_found_text = config.selection.how_found_options[int(how_found_idx)]
    except (IndexError, ValueError):
        how_found_text = "Не указано"
    
    department_key = dialog_data.get("selected_department", "")
    department_name = ""
    position_text = ""
    
    if department_key in config.selection.departments:
        dept_info = config.selection.departments[department_key]
        department_name = dept_info.get("name", "")
        
        position_idx = dialog_data.get("selected_position", "0")
        positions = dept_info.get("positions", [])
        try:
            position_text = positions[int(position_idx)]
        except (IndexError, ValueError):
            position_text = "Не указано"
    
    course = dialog_data.get("course", "1")
    
    # Определяем статус резюме
    if "resume_file" in dialog_data:
        resume_filename = dialog_data.get("resume_file", "")
        resume_status = f"✅ Загружено: {resume_filename}"
    else:
        resume_status = "❌ Не загружено"
    
    return {
        "full_name": dialog_data.get("full_name", ""),
        "university": dialog_data.get("university", ""),
        "course_text": f"{course} курс",
        "phone": dialog_data.get("phone", ""),
        "email": dialog_data.get("email", ""),
        "how_found_text": how_found_text,
        "department_name": department_name,
        "position_text": position_text,
        "experience": dialog_data.get("experience", ""),
        "motivation": dialog_data.get("motivation", ""),
        "resume_status": resume_status
    }
