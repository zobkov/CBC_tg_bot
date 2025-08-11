from aiogram_dialog import DialogManager
from config.config import load_config


async def get_departments_list(dialog_manager: DialogManager, **kwargs):
    """Получить список департаментов для выбора"""
    config = load_config()
    departments = []
    
    for dept_key, dept_data in config.selection.departments.items():
        departments.append((dept_key, dept_data["name"]))
    
    return {
        "departments": departments,
    }


async def get_positions_for_department(dialog_manager: DialogManager, **kwargs):
    """Получить список позиций для выбранного департамента"""
    config = load_config()
    
    # Получаем выбранный департамент из состояния
    selected_dept = dialog_manager.dialog_data.get("selected_department")
    if not selected_dept:
        return {"positions": [], "selected_department": ""}
    
    # Получаем позиции для департамента
    dept_data = config.selection.departments.get(selected_dept, {})
    positions = []
    
    # Позиции теперь хранятся как массив, а не объект
    positions_list = dept_data.get("positions", [])
    for i, pos_name in enumerate(positions_list):
        positions.append((str(i), pos_name))  # используем индекс как ID
    
    # Получаем название департамента
    dept_name = dept_data.get("name", selected_dept)
    
    return {
        "positions": positions,
        "selected_department": dept_name,
    }


async def get_priorities_overview(dialog_manager: DialogManager, **kwargs):
    """Получить обзор всех выбранных приоритетов"""
    data = dialog_manager.dialog_data
    config = load_config()
    
    priorities_text = ""
    priorities_count = 0
    
    # Формируем текст с приоритетами
    for i in range(1, 4):
        dept_key = data.get(f"priority_{i}_department")
        pos_index = data.get(f"priority_{i}_position")
        
        if dept_key and pos_index is not None:
            priorities_count += 1
            dept_name = config.selection.departments.get(dept_key, {}).get("name", dept_key)
            
            # Получаем позицию по индексу из массива
            positions_list = config.selection.departments.get(dept_key, {}).get("positions", [])
            try:
                pos_name = positions_list[int(pos_index)]
            except (IndexError, ValueError):
                pos_name = "Неизвестная позиция"
                
            priorities_text += f"🥇 <b>{i}-й приоритет:</b> {dept_name} - {pos_name}\n"
        else:
            priorities_text += f"⚪ <b>{i}-й приоритет:</b> <i>не выбран</i>\n"
    
    # Добавим информацию для дебага
    print(f"DEBUG: priorities_count = {priorities_count}")
    print(f"DEBUG: dialog_data = {data}")
    
    return {
        "priorities_text": priorities_text,
        "priorities_count": priorities_count,
        "can_add_2": priorities_count >= 1 and not data.get("priority_2_department"),
        "can_add_3": priorities_count >= 2 and not data.get("priority_3_department"),
    }


async def get_edit_departments_list(dialog_manager: DialogManager, **kwargs):
    """Получить список департаментов для редактирования (то же что и обычный список)"""
    return await get_departments_list(dialog_manager, **kwargs)


async def get_edit_positions_for_department(dialog_manager: DialogManager, **kwargs):
    """Получить список позиций для редактирования выбранного департамента"""
    config = load_config()
    
    # Получаем выбранный департамент из состояния редактирования
    selected_dept = dialog_manager.dialog_data.get("edit_selected_department")
    if not selected_dept:
        return {"positions": [], "selected_department": ""}
    
    # Получаем позиции для департамента
    dept_data = config.selection.departments.get(selected_dept, {})
    positions = []
    
    # Позиции хранятся как массив
    positions_list = dept_data.get("positions", [])
    for i, pos_name in enumerate(positions_list):
        positions.append((str(i), pos_name))  # используем индекс как ID
    
    # Получаем название департамента
    dept_name = dept_data.get("name", selected_dept)
    
    return {
        "positions": positions,
        "selected_department": dept_name,
    }
