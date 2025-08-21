from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType
import json
import os

from app.utils.optimized_dialog_widgets import get_file_id_for_path


def load_departments_config():
    """Загр    # Определяем путь к изображению отдела
    department_images = {
        "creative": "choose_department/creative/творческий.png",
        "design": "choose_department/design/дизайн.png", 
        "exhibition": "choose_department/exhibition/выставочный.png",
        "logistics_it": "choose_department/logistics/логистика.png",
        "partners": "choose_department/partners/партнеры.png",
        "program": "choose_department/program/программа.png",
        "smm_pr": "choose_department/smmpr/smm.png"
    }игурацию отделов"""
    config_path = os.path.join(os.path.dirname(__file__), '../../../../config/departments.json')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def get_departments_list(dialog_manager: DialogManager, **kwargs):
    """Получить список департаментов для выбора"""
    config = load_departments_config()
    departments = []
    
    for dept_key, dept_data in config["departments"].items():
        departments.append((dept_key, dept_data["name"]))
    
    return {
        "departments": departments,
    }


async def get_subdepartments_list(dialog_manager: DialogManager, **kwargs):
    """Получить список под-отделов для выбранного департамента"""
    config = load_departments_config()
    
    # Получаем выбранный департамент из состояния
    selected_dept = dialog_manager.dialog_data.get("selected_department")
    if not selected_dept:
        return {"subdepartments": [], "selected_department": "", "department_description": ""}
    
    dept_data = config["departments"].get(selected_dept, {})
    subdepartments = []
    
    # Если есть под-отделы
    if "subdepartments" in dept_data:
        for subdept_key, subdept_data in dept_data["subdepartments"].items():
            subdepartments.append((subdept_key, subdept_data["name"]))
    
    return {
        "subdepartments": subdepartments,
        "selected_department": dept_data.get("name", selected_dept),
        "department_description": dept_data.get("description", "")
    }


def _is_vacancy_already_selected(dialog_data, dept_key, subdept_key, pos_index, exclude_priority=None):
    """Проверить, выбрана ли уже данная вакансия"""
    current_vacancy = (dept_key, subdept_key, pos_index)
    
    # Проверяем все приоритеты
    for i in range(1, 4):
        # Пропускаем проверку для редактируемого приоритета
        if exclude_priority and i == exclude_priority:
            continue
            
        dept = dialog_data.get(f"priority_{i}_department")
        subdept = dialog_data.get(f"priority_{i}_subdepartment")
        pos = dialog_data.get(f"priority_{i}_position")
        
        if dept and pos is not None:
            stored_vacancy = (dept, subdept, str(pos))
            if stored_vacancy == current_vacancy:
                return True
    
    return False


async def get_positions_for_department(dialog_manager: DialogManager, **kwargs):
    """Получить список позиций для выбранного департамента или под-отдела"""
    config = load_departments_config()
    
    # Получаем выбранный департамент и под-отдел из состояния
    selected_dept = dialog_manager.dialog_data.get("selected_department")
    selected_subdept = dialog_manager.dialog_data.get("selected_subdepartment")
    
    print(f"DEBUG: get_positions_for_department - selected_dept={selected_dept}, selected_subdept={selected_subdept}")
    
    if not selected_dept:
        return {"positions": [], "selected_department": "", "department_description": ""}
    
    dept_data = config["departments"].get(selected_dept, {})
    positions = []
    department_name = dept_data.get("name", selected_dept)
    department_description = dept_data.get("description", "")
    
    # Если выбран под-отдел
    if selected_subdept and "subdepartments" in dept_data:
        subdept_data = dept_data["subdepartments"].get(selected_subdept, {})
        positions_list = subdept_data.get("positions", [])
        department_name = f"{department_name} - {subdept_data.get('name', selected_subdept)}"
        department_description = subdept_data.get("description", department_description)
        print(f"DEBUG: Using subdepartment positions - subdept={selected_subdept}, positions_count={len(positions_list)}")
    else:
        # Берем позиции напрямую из отдела
        positions_list = dept_data.get("positions", [])
        print(f"DEBUG: Using department positions - dept={selected_dept}, positions_count={len(positions_list)}")
    
    print(f"DEBUG: positions_list = {positions_list}")
    
    dialog_data = dialog_manager.dialog_data
    
    # Определяем, какой приоритет мы сейчас выбираем, чтобы исключить его из проверки
    current_state = dialog_manager.current_context().state.state
    exclude_priority = None
    if current_state == "JobSelectionSG:select_position":
        exclude_priority = 1
    elif current_state == "JobSelectionSG:select_position_2":
        exclude_priority = 2
    elif current_state == "JobSelectionSG:select_position_3":
        exclude_priority = 3
    
    for i, pos_name in enumerate(positions_list):
        # Проверяем, не выбрана ли уже эта позиция
        if not _is_vacancy_already_selected(dialog_data, selected_dept, selected_subdept, str(i), exclude_priority):
            positions.append((str(i), pos_name))
    
    print(f"DEBUG: final positions = {positions}")
    
    return {
        "positions": positions,
        "selected_department": department_name,
        "department_description": department_description
    }


async def get_priorities_overview(dialog_manager: DialogManager, **kwargs):
    """Получить обзор всех выбранных приоритетов"""
    data = dialog_manager.dialog_data
    config = load_departments_config()
    
    priorities_text = ""
    priorities_count = 0
    
    # Формируем текст с приоритетами
    for i in range(1, 4):
        dept_key = data.get(f"priority_{i}_department")
        subdept_key = data.get(f"priority_{i}_subdepartment")
        pos_index = data.get(f"priority_{i}_position")
        
        if dept_key and pos_index is not None:
            priorities_count += 1
            dept_data = config["departments"].get(dept_key, {})
            dept_name = dept_data.get("name", dept_key)
            
            # Если есть под-отдел
            if subdept_key and "subdepartments" in dept_data:
                subdept_data = dept_data["subdepartments"].get(subdept_key, {})
                positions_list = subdept_data.get("positions", [])
                full_dept_name = f"{dept_name} - {subdept_data.get('name', subdept_key)}"
            else:
                positions_list = dept_data.get("positions", [])
                full_dept_name = dept_name
            
            # Получаем позицию по индексу из массива
            try:
                pos_name = positions_list[int(pos_index)]
            except (IndexError, ValueError):
                pos_name = "Неизвестная позиция"
                
            priorities_text += f"🥇 <b>{i}-й приоритет:</b> {full_dept_name} - {pos_name}\n"
        else:
            priorities_text += f"⚪ <b>{i}-й приоритет:</b> <i>не выбран</i>\n"
    
    return {
        "priorities_text": priorities_text,
        "priorities_count": priorities_count,
        "can_add_2": priorities_count >= 1 and not data.get("priority_2_department"),
        "can_add_3": priorities_count >= 2 and not data.get("priority_3_department"),
    }


async def get_edit_departments_list(dialog_manager: DialogManager, **kwargs):
    """Получить список департаментов для редактирования (то же что и обычный список)"""
    return await get_departments_list(dialog_manager, **kwargs)


async def get_edit_subdepartments_list(dialog_manager: DialogManager, **kwargs):
    """Получить список под-отделов для редактирования"""
    config = load_departments_config()
    
    # Получаем выбранный департамент из состояния редактирования
    selected_dept = dialog_manager.dialog_data.get("edit_selected_department")
    if not selected_dept:
        return {"subdepartments": [], "selected_department": "", "department_description": ""}
    
    dept_data = config["departments"].get(selected_dept, {})
    subdepartments = []
    
    # Если есть под-отделы
    if "subdepartments" in dept_data:
        for subdept_key, subdept_data in dept_data["subdepartments"].items():
            subdepartments.append((subdept_key, subdept_data["name"]))
    
    return {
        "subdepartments": subdepartments,
        "selected_department": dept_data.get("name", selected_dept),
        "department_description": dept_data.get("description", "")
    }


async def get_edit_positions_for_department(dialog_manager: DialogManager, **kwargs):
    """Получить список позиций для редактирования выбранного департамента/под-отдела"""
    config = load_departments_config()
    
    # Получаем выбранный департамент и под-отдел из состояния редактирования
    selected_dept = dialog_manager.dialog_data.get("edit_selected_department")
    selected_subdept = dialog_manager.dialog_data.get("edit_selected_subdepartment")
    
    if not selected_dept:
        return {"positions": [], "selected_department": "", "department_description": ""}
    
    dept_data = config["departments"].get(selected_dept, {})
    positions = []
    department_name = dept_data.get("name", selected_dept)
    department_description = dept_data.get("description", "")
    
    # Если выбран под-отдел
    if selected_subdept and "subdepartments" in dept_data:
        subdept_data = dept_data["subdepartments"].get(selected_subdept, {})
        positions_list = subdept_data.get("positions", [])
        department_name = f"{department_name} - {subdept_data.get('name', selected_subdept)}"
        department_description = subdept_data.get("description", department_description)
    else:
        # Берем позиции напрямую из отдела
        positions_list = dept_data.get("positions", [])
    
    dialog_data = dialog_manager.dialog_data
    editing_priority = dialog_data.get("editing_priority", 1)
    
    for i, pos_name in enumerate(positions_list):
        # Проверяем, не выбрана ли уже эта позиция
        # (исключая редактируемый приоритет)
        if not _is_vacancy_already_selected(dialog_data, selected_dept, selected_subdept, str(i), exclude_priority=editing_priority):
            positions.append((str(i), pos_name))
    
    return {
        "positions": positions,
        "selected_department": department_name,
        "department_description": department_description
    }


async def get_department_selection_media(dialog_manager: DialogManager, **kwargs):
    """Получаем медиа для окна выбора отдела"""
    file_id = get_file_id_for_path("choose_department/отделы.png")
    
    if file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path="app/bot/assets/images/choose_department/отделы.png"
        )
    
    return {
        "media": media
    }


async def get_subdepartment_media(dialog_manager: DialogManager, **kwargs):
    """Получаем медиа для под-отдела на основе выбранного отдела"""
    selected_dept = dialog_manager.dialog_data.get("selected_department")
    
    if not selected_dept:
        # Fallback изображение
        return await get_department_selection_media(dialog_manager, **kwargs)
    
    # Определяем путь к изображению отдела
    department_images = {
        "creative": "choose_department/creative/творческий.png",
        "design": "choose_department/design/дизайн.png", 
        "exhibition": "choose_department/exhibition/exhibition.png",
        "logistics_it": "choose_department/logistics/логистика.png",
        "partners": "choose_department/partners/partners.png",
        "program": "choose_department/program/program.png",
        "smm_pr": "choose_department/smmpr/sммрр.png"
    }
    
    image_path = department_images.get(selected_dept, "choose_department/отделы.png")
    file_id = get_file_id_for_path(image_path)
    
    if file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path=f"app/bot/assets/images/{image_path}"
        )
    
    return {
        "media": media
    }


async def get_position_media(dialog_manager: DialogManager, **kwargs):
    """Получаем медиа для позиций на основе выбранного отдела и под-отдела"""
    selected_dept = dialog_manager.dialog_data.get("selected_department")
    selected_subdept = dialog_manager.dialog_data.get("selected_subdepartment")
    
    if not selected_dept:
        return await get_department_selection_media(dialog_manager, **kwargs)
    
    # Базовые изображения для отделов без подотделов
    department_position_images = {
        "design": "choose_position/design/ДИЗАЙН.png",
        "exhibition": "choose_position/exhibition/ВЫСТАВКИ.png", 
        "logistics_it": "choose_position/logistics/ЛОГИСТИКА.png",
        "partners": "choose_position/partners/ПАРТНЕРЫ.png",
        "program": "choose_position/program/ПРОГРАММА.png"
    }
    
    # Для отделов с подотделами
    if selected_dept in ["creative", "smm_pr"] and selected_subdept:
        if selected_dept == "creative":
            subdept_images = {
                "stage": "choose_position/creative/ТВОРЧЕСКИЙ_сцена_1.png",
                "booth": "choose_position/creative/ТВОРЧЕСКИЙ_стенд.png"
            }
            image_path = subdept_images.get(selected_subdept, "choose_position/creative/ТВОРЧЕСКИЙ_сцена_1.png")
        elif selected_dept == "smm_pr":
            subdept_images = {
                "social": "choose_position/smmpr/СММ_соцсети_1.png", 
                "media": "choose_position/smmpr/СММ_шоу_1.png"
            }
            image_path = subdept_images.get(selected_subdept, "choose_position/smmpr/СММ_соцсети_1.png")
    else:
        # Обычные отделы
        image_path = department_position_images.get(selected_dept, "choose_department/отделы.png")
    
    file_id = get_file_id_for_path(image_path)
    
    if file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path=f"app/bot/assets/images/{image_path}"
        )
    
    return {
        "media": media
    }


# Функции для редактирования (аналогичные основным, но используют edit_ префиксы)
async def get_edit_subdepartment_media(dialog_manager: DialogManager, **kwargs):
    """Получаем медиа для под-отдела при редактировании"""
    selected_dept = dialog_manager.dialog_data.get("edit_selected_department")
    
    if not selected_dept:
        return await get_department_selection_media(dialog_manager, **kwargs)
    
    department_images = {
        "creative": "choose_department/creative/творческий.png",
        "design": "choose_department/design/дизайн.png",
        "exhibition": "choose_department/exhibition/выставочный.png", 
        "logistics_it": "choose_department/logistics/логистика.png",
        "partners": "choose_department/partners/партнеры.png",
        "program": "choose_department/program/программа.png",
        "smm_pr": "choose_department/smmpr/smm.png"
    }
    
    image_path = department_images.get(selected_dept, "choose_department/отделы.png")
    file_id = get_file_id_for_path(image_path)
    
    if file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path=f"app/bot/assets/images/{image_path}"
        )
    
    return {
        "media": media
    }


async def get_edit_position_media(dialog_manager: DialogManager, **kwargs):
    """Получаем медиа для позиций при редактировании"""
    selected_dept = dialog_manager.dialog_data.get("edit_selected_department")
    selected_subdept = dialog_manager.dialog_data.get("edit_selected_subdepartment")
    
    if not selected_dept:
        return await get_department_selection_media(dialog_manager, **kwargs)
    
    department_position_images = {
        "design": "choose_position/design/ДИЗАЙН.png",
        "exhibition": "choose_position/exhibition/ВЫСТАВКИ.png",
        "logistics_it": "choose_position/logistics/ЛОГИСТИКА.png", 
        "partners": "choose_position/partners/ПАРТНЕРЫ.png",
        "program": "choose_position/program/ПРОГРАММА.png"
    }
    
    if selected_dept in ["creative", "smm_pr"] and selected_subdept:
        if selected_dept == "creative":
            subdept_images = {
                "stage": "choose_position/creative/ТВОРЧЕСКИЙ_сцена_1.png",
                "booth": "choose_position/creative/ТВОРЧЕСКИЙ_стенд.png"
            }
            image_path = subdept_images.get(selected_subdept, "choose_position/creative/ТВОРЧЕСКИЙ_сцена_1.png")
        elif selected_dept == "smm_pr":
            subdept_images = {
                "social": "choose_position/smmpr/СММ_соцсети_1.png",
                "media": "choose_position/smmpr/СММ_шоу_1.png" 
            }
            image_path = subdept_images.get(selected_subdept, "choose_position/smmpr/СММ_соцсети_1.png")
    else:
        image_path = department_position_images.get(selected_dept, "choose_department/отделы.png")
    
    file_id = get_file_id_for_path(image_path)
    
    if file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path=f"app/bot/assets/images/{image_path}"
        )
    
    return {
        "media": media
    }
