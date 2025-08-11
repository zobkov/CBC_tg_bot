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
        return {"how_found_options": [], "has_selections": False}
    
    options = []
    for i, option in enumerate(config.selection.how_found_options):
        options.append({"id": str(i), "text": option})
    
    # Проверяем, есть ли выбранные опции через Multiselect
    multiselect = dialog_manager.find("how_found_multiselect")
    has_selections = False
    was_in_kbk = False
    
    if multiselect:
        checked_items = multiselect.get_checked()
        has_selections = len(checked_items) > 0
        was_in_kbk = "6" in checked_items  # Индекс опции "Ранее участвовал в КБК (2024-2025)"
    
    return {
        "how_found_options": options,
        "has_selections": has_selections,
        "was_in_kbk": was_in_kbk
    }


async def get_departments_for_previous(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем список департаментов для выбора предыдущего участия"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"departments": [], "was_in_kbk": False, "departments_description": ""}
    
    departments = []
    descriptions = []
    
    for key, dept_info in config.selection.departments.items():
        departments.append({
            "id": key, 
            "text": dept_info["name"],
            "description": dept_info.get("description", "")
        })
        
        # Формируем описание для текста
        descriptions.append(f"<b>{dept_info['name']}</b>\n{dept_info.get('description', '')}")
    
    departments_description = "\n\n".join(descriptions)
    
    # Проверяем, выбрал ли пользователь "Ранее участвовал в КБК" через Multiselect
    multiselect = dialog_manager.find("how_found_multiselect")
    was_in_kbk = False
    
    if multiselect:
        checked_items = multiselect.get_checked()
        was_in_kbk = "6" in checked_items  # Индекс опции "Ранее участвовал в КБК (2024-2025)"
    
    return {
        "departments": departments,
        "was_in_kbk": was_in_kbk,
        "departments_description": departments_description
    }


async def get_departments(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем список департаментов"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"departments": [], "departments_description": ""}
    
    departments = []
    descriptions = []
    
    for key, dept_info in config.selection.departments.items():
        departments.append({
            "id": key, 
            "text": dept_info["name"],
            "description": dept_info.get("description", "")
        })
        
        # Формируем описание для текста
        descriptions.append(f"<b>{dept_info['name']}</b>\n{dept_info.get('description', '')}")
    
    departments_description = "\n\n".join(descriptions)
    
    return {
        "departments": departments,
        "departments_description": departments_description
    }


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
    
    # Получаем множественные варианты "Откуда узнали" из Multiselect
    multiselect = dialog_manager.find("how_found_multiselect")
    how_found_selections = set()
    
    if multiselect:
        how_found_selections = set(multiselect.get_checked())
    else:
        # Fallback к dialog_data если Multiselect не найден
        how_found_selections = dialog_data.get("how_found_selections", set())
    
    how_found_texts = []
    for selection in how_found_selections:
        try:
            idx = int(selection)
            if idx < len(config.selection.how_found_options):
                how_found_texts.append(config.selection.how_found_options[idx])
        except (ValueError, IndexError):
            continue
    
    how_found_text = ", ".join(how_found_texts) if how_found_texts else "Не указано"
    
    # Получаем информацию о предыдущем отделе, если участвовал в КБК
    previous_dept_text = ""
    if "6" in how_found_selections:  # "Ранее участвовал в КБК"
        previous_dept_key = dialog_data.get("previous_department", "")
        if previous_dept_key and previous_dept_key in config.selection.departments:
            previous_dept_text = f"\n🏢 <b>Предыдущий отдел в КБК:</b> {config.selection.departments[previous_dept_key]['name']}"
    
    # Формируем информацию о приоритетах вакансий
    priorities_summary = ""
    priorities_exist = False
    
    for i in range(1, 4):
        dept_key = dialog_data.get(f"priority_{i}_department")
        pos_index = dialog_data.get(f"priority_{i}_position")
        
        if dept_key and pos_index is not None:
            priorities_exist = True
            dept_name = config.selection.departments.get(dept_key, {}).get("name", dept_key)
            
            # Получаем позицию по индексу из массива
            positions_list = config.selection.departments.get(dept_key, {}).get("positions", [])
            try:
                pos_name = positions_list[int(pos_index)]
            except (IndexError, ValueError):
                pos_name = "Неизвестная позиция"
                
            priorities_summary += f"  {i}. {dept_name} - {pos_name}\n"
        else:
            priorities_summary += f"  {i}. Не выбрано\n"
    
    if not priorities_exist:
        priorities_summary = "❌ Вакансии не выбраны"
    
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
        "previous_dept_text": previous_dept_text,
        "priorities_summary": priorities_summary,
        "experience": dialog_data.get("experience", ""),
        "motivation": dialog_data.get("motivation", ""),
        "resume_status": resume_status
    }


async def get_edit_menu_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем данные для меню редактирования"""
    dialog_data = dialog_manager.dialog_data
    
    # Проверяем, участвовал ли пользователь в КБК (для показа кнопки редактирования предыдущего отдела)
    selected_options = dialog_data.get("how_found_selections", set())
    was_in_kbk = "6" in selected_options
    
    return {
        "was_in_kbk": was_in_kbk,
        "full_name": dialog_data.get("full_name", "Не указано"),
        "university": dialog_data.get("university", "Не указано"),
        "course": dialog_data.get("course", "1"),
        "phone": dialog_data.get("phone", "Не указано"),
        "email": dialog_data.get("email", "Не указано"),
        "experience": dialog_data.get("experience", "Не указано")[:50] + "..." if len(dialog_data.get("experience", "")) > 50 else dialog_data.get("experience", "Не указано"),
        "motivation": dialog_data.get("motivation", "Не указано")[:50] + "..." if len(dialog_data.get("motivation", "")) > 50 else dialog_data.get("motivation", "Не указано")
    }


async def get_edit_how_found_options(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем варианты ответов на вопрос 'Откуда узнали о КБК' для редактирования"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {"how_found_options": [], "has_selections": False}
    
    options = []
    for i, option in enumerate(config.selection.how_found_options):
        options.append({"id": str(i), "text": option})
    
    # Проверяем текущие выборы для предустановки
    dialog_data = dialog_manager.dialog_data
    selected_options = dialog_data.get("how_found_selections", set())
    has_selections = len(selected_options) > 0
    
    return {
        "how_found_options": options,
        "has_selections": has_selections
    }
