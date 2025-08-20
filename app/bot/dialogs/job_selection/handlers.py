from typing import Any
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
import json
import os

from app.bot.states.job_selection import JobSelectionSG
from app.bot.states.first_stage import FirstStageSG


def load_departments_config():
    """Загрузить конфигурацию отделов"""
    config_path = os.path.join(os.path.dirname(__file__), '../../../../config/departments.json')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def on_department_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Обработчик выбора департамента"""
    config = load_departments_config()
    current_state = dialog_manager.current_context().state.state
    
    print(f"DEBUG: on_department_selected called")
    print(f"DEBUG: current_state = {current_state}")
    print(f"DEBUG: item_id = {item_id}")
    
    dialog_manager.dialog_data["selected_department"] = item_id
    
    # Проверяем, есть ли у отдела под-отделы
    dept_data = config["departments"].get(item_id, {})
    has_subdepartments = "subdepartments" in dept_data
    
    if current_state == JobSelectionSG.select_department.state:
        dialog_manager.dialog_data["priority_1_department"] = item_id
        if has_subdepartments:
            await dialog_manager.switch_to(JobSelectionSG.select_subdepartment)
        else:
            await dialog_manager.switch_to(JobSelectionSG.select_position)
    elif current_state == JobSelectionSG.select_department_2.state:
        dialog_manager.dialog_data["priority_2_department"] = item_id
        if has_subdepartments:
            await dialog_manager.switch_to(JobSelectionSG.select_subdepartment_2)
        else:
            await dialog_manager.switch_to(JobSelectionSG.select_position_2)
    elif current_state == JobSelectionSG.select_department_3.state:
        dialog_manager.dialog_data["priority_3_department"] = item_id
        if has_subdepartments:
            await dialog_manager.switch_to(JobSelectionSG.select_subdepartment_3)
        else:
            await dialog_manager.switch_to(JobSelectionSG.select_position_3)


async def on_subdepartment_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Обработчик выбора под-отдела"""
    current_state = dialog_manager.current_context().state.state
    
    print(f"DEBUG: on_subdepartment_selected called")
    print(f"DEBUG: current_state = {current_state}")
    print(f"DEBUG: item_id = {item_id}")
    
    dialog_manager.dialog_data["selected_subdepartment"] = item_id
    
    if current_state == JobSelectionSG.select_subdepartment.state:
        dialog_manager.dialog_data["priority_1_subdepartment"] = item_id
        await dialog_manager.switch_to(JobSelectionSG.select_position)
    elif current_state == JobSelectionSG.select_subdepartment_2.state:
        dialog_manager.dialog_data["priority_2_subdepartment"] = item_id
        await dialog_manager.switch_to(JobSelectionSG.select_position_2)
    elif current_state == JobSelectionSG.select_subdepartment_3.state:
        dialog_manager.dialog_data["priority_3_subdepartment"] = item_id
        await dialog_manager.switch_to(JobSelectionSG.select_position_3)


async def on_position_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Обработчик выбора позиции"""
    current_state = dialog_manager.current_context().state.state
    
    print(f"DEBUG: on_position_selected called")
    print(f"DEBUG: current_state = {current_state}")
    print(f"DEBUG: item_id = {item_id}")
    
    if current_state == JobSelectionSG.select_position.state:
        dialog_manager.dialog_data["priority_1_position"] = item_id
        await dialog_manager.switch_to(JobSelectionSG.priorities_overview)
    elif current_state == JobSelectionSG.select_position_2.state:
        dialog_manager.dialog_data["priority_2_position"] = item_id
        await dialog_manager.switch_to(JobSelectionSG.select_department_3)
    elif current_state == JobSelectionSG.select_position_3.state:
        dialog_manager.dialog_data["priority_3_position"] = item_id
        await dialog_manager.switch_to(JobSelectionSG.priorities_overview)


async def on_priority_confirmed(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик подтверждения выбора приоритетов"""
    print(f"DEBUG: on_priority_confirmed called")
    print(f"DEBUG: dialog_data before processing = {dialog_manager.dialog_data}")
    
    # Получаем исходные данные формы переданные при запуске диалога
    original_form_data = dict(dialog_manager.start_data or {})
    
    # Сохраняем данные приоритетов в основные данные заявки
    priority_data = {}
    
    for i in range(1, 4):
        dept_key = dialog_manager.dialog_data.get(f"priority_{i}_department")
        subdept_key = dialog_manager.dialog_data.get(f"priority_{i}_subdepartment")
        pos_index = dialog_manager.dialog_data.get(f"priority_{i}_position")
        
        if dept_key and pos_index is not None:
            priority_data[f"priority_{i}_department"] = dept_key
            if subdept_key:
                priority_data[f"priority_{i}_subdepartment"] = subdept_key
            priority_data[f"priority_{i}_position"] = pos_index
    
    print(f"DEBUG: priority_data to save = {priority_data}")
    
    # Объединяем исходные данные формы с новыми данными приоритетов
    combined_data = {**original_form_data, **priority_data}
    
    # Сохраняем приоритеты в родительском диалоге
    dialog_manager.dialog_data.update(priority_data)
    
    # Закрываем диалог выбора вакансий и возвращаемся к первому этапу
    await dialog_manager.done(result=priority_data)


async def on_edit_priority_1(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик редактирования первого приоритета"""
    dialog_manager.dialog_data["editing_priority"] = 1
    await dialog_manager.switch_to(JobSelectionSG.edit_priority_1)


async def on_edit_priority_2(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик редактирования второго приоритета"""
    dialog_manager.dialog_data["editing_priority"] = 2
    await dialog_manager.switch_to(JobSelectionSG.edit_priority_2)


async def on_edit_priority_3(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик редактирования третьего приоритета"""
    dialog_manager.dialog_data["editing_priority"] = 3
    await dialog_manager.switch_to(JobSelectionSG.edit_priority_3)


async def on_edit_department_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Обработчик выбора департамента при редактировании"""
    config = load_departments_config()
    
    dialog_manager.dialog_data["edit_selected_department"] = item_id
    
    # Проверяем, есть ли у отдела под-отделы
    dept_data = config["departments"].get(item_id, {})
    has_subdepartments = "subdepartments" in dept_data
    
    # Определяем какой приоритет редактируется
    editing_priority = dialog_manager.dialog_data.get("editing_priority", 1)
    
    if has_subdepartments:
        if editing_priority == 1:
            await dialog_manager.switch_to(JobSelectionSG.edit_priority_1_subdepartment)
        elif editing_priority == 2:
            await dialog_manager.switch_to(JobSelectionSG.edit_priority_2_subdepartment)
        elif editing_priority == 3:
            await dialog_manager.switch_to(JobSelectionSG.edit_priority_3_subdepartment)
    else:
        if editing_priority == 1:
            await dialog_manager.switch_to(JobSelectionSG.edit_priority_1_position)
        elif editing_priority == 2:
            await dialog_manager.switch_to(JobSelectionSG.edit_priority_2_position)
        elif editing_priority == 3:
            await dialog_manager.switch_to(JobSelectionSG.edit_priority_3_position)


async def on_edit_subdepartment_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Обработчик выбора под-отдела при редактировании"""
    dialog_manager.dialog_data["edit_selected_subdepartment"] = item_id
    
    # Определяем какой приоритет редактируется
    editing_priority = dialog_manager.dialog_data.get("editing_priority", 1)
    
    if editing_priority == 1:
        await dialog_manager.switch_to(JobSelectionSG.edit_priority_1_position)
    elif editing_priority == 2:
        await dialog_manager.switch_to(JobSelectionSG.edit_priority_2_position)
    elif editing_priority == 3:
        await dialog_manager.switch_to(JobSelectionSG.edit_priority_3_position)


async def on_edit_position_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Обработчик выбора позиции при редактировании"""
    editing_priority = dialog_manager.dialog_data.get("editing_priority", 1)
    edit_dept = dialog_manager.dialog_data.get("edit_selected_department")
    edit_subdept = dialog_manager.dialog_data.get("edit_selected_subdepartment")
    
    # Сохраняем изменения
    dialog_manager.dialog_data[f"priority_{editing_priority}_department"] = edit_dept
    if edit_subdept:
        dialog_manager.dialog_data[f"priority_{editing_priority}_subdepartment"] = edit_subdept
    else:
        # Удаляем под-отдел если он не выбран
        dialog_manager.dialog_data.pop(f"priority_{editing_priority}_subdepartment", None)
    dialog_manager.dialog_data[f"priority_{editing_priority}_position"] = item_id
    
    # Очищаем временные данные редактирования
    dialog_manager.dialog_data.pop("editing_priority", None)
    dialog_manager.dialog_data.pop("edit_selected_department", None)
    dialog_manager.dialog_data.pop("edit_selected_subdepartment", None)
    
    # Возвращаемся к обзору приоритетов
    await dialog_manager.switch_to(JobSelectionSG.priorities_overview)


async def on_swap_priorities(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик перехода к меню выбора приоритетов для обмена"""
    await dialog_manager.switch_to(JobSelectionSG.swap_priorities_menu)


async def on_swap_1_2(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик обмена 1-го и 2-го приоритетов"""
    data = dialog_manager.dialog_data
    
    # Обмениваем местами 1-й и 2-й приоритеты
    temp_dept = data.get("priority_1_department")
    temp_subdept = data.get("priority_1_subdepartment")
    temp_pos = data.get("priority_1_position")
    
    data["priority_1_department"] = data.get("priority_2_department")
    data["priority_1_subdepartment"] = data.get("priority_2_subdepartment")
    data["priority_1_position"] = data.get("priority_2_position")
    
    data["priority_2_department"] = temp_dept
    data["priority_2_subdepartment"] = temp_subdept
    data["priority_2_position"] = temp_pos
    
    # Возвращаемся к обзору приоритетов
    await dialog_manager.switch_to(JobSelectionSG.priorities_overview)


async def on_swap_1_3(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик обмена 1-го и 3-го приоритетов"""
    data = dialog_manager.dialog_data
    
    # Обмениваем местами 1-й и 3-й приоритеты
    temp_dept = data.get("priority_1_department")
    temp_subdept = data.get("priority_1_subdepartment")
    temp_pos = data.get("priority_1_position")
    
    data["priority_1_department"] = data.get("priority_3_department")
    data["priority_1_subdepartment"] = data.get("priority_3_subdepartment")
    data["priority_1_position"] = data.get("priority_3_position")
    
    data["priority_3_department"] = temp_dept
    data["priority_3_subdepartment"] = temp_subdept
    data["priority_3_position"] = temp_pos
    
    # Возвращаемся к обзору приоритетов
    await dialog_manager.switch_to(JobSelectionSG.priorities_overview)


async def on_swap_2_3(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик обмена 2-го и 3-го приоритетов"""
    data = dialog_manager.dialog_data
    
    # Обмениваем местами 2-й и 3-й приоритеты
    temp_dept = data.get("priority_2_department")
    temp_subdept = data.get("priority_2_subdepartment")
    temp_pos = data.get("priority_2_position")
    
    data["priority_2_department"] = data.get("priority_3_department")
    data["priority_2_subdepartment"] = data.get("priority_3_subdepartment")
    data["priority_2_position"] = data.get("priority_3_position")
    
    data["priority_3_department"] = temp_dept
    data["priority_3_subdepartment"] = temp_subdept
    data["priority_3_position"] = temp_pos
    
    # Возвращаемся к обзору приоритетов
    await dialog_manager.switch_to(JobSelectionSG.priorities_overview)


async def on_back_to_priorities_overview(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик возврата к обзору приоритетов"""
    await dialog_manager.switch_to(JobSelectionSG.priorities_overview)


async def on_add_priority_2(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик добавления второго приоритета"""
    await dialog_manager.switch_to(JobSelectionSG.select_department_2)


async def on_add_priority_3(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик добавления третьего приоритета"""
    await dialog_manager.switch_to(JobSelectionSG.select_department_3)
