from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Select, Row, Back, Next, Cancel, Start, Button, Column, Group
from aiogram_dialog.widgets.input import MessageInput

from app.bot.states.job_selection import JobSelectionSG
from app.bot.states.first_stage import FirstStageSG
from .getters import (
    get_departments_list, get_positions_for_department, get_priorities_overview,
    get_edit_departments_list, get_edit_positions_for_department
)
from .handlers import (
    on_department_selected, on_position_selected, on_priority_confirmed,
    on_edit_priority_1, on_edit_priority_2, on_edit_priority_3,
    on_swap_priorities, on_edit_department_selected, on_edit_position_selected,
    on_save_edited_priority, on_start_over, on_add_priority_2, on_add_priority_3,
    on_swap_1_2, on_swap_1_3, on_swap_2_3, on_back_to_priorities_overview
)

job_selection_dialog = Dialog(
    # Выбор департамента для первого приоритета
    Window(
        Const("🏢 Выберите департамент для вашей <b>первой приоритетной</b> вакансии:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_department_selected,
            ),
        ),
        Cancel(Const("❌ Отмена"), result="cancel"),
        state=JobSelectionSG.select_department,
        getter=get_departments_list,
    ),
    
    # Выбор позиции для первого приоритета
    Window(
        Format("👨‍💼 Выберите позицию в департаменте <b>{selected_department}</b>:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_position_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад к департаментам")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.select_position,
        getter=get_positions_for_department,
    ),
    
    # Выбор департамента для второго приоритета
    Window(
        Const("🏢 Выберите департамент для вашей <b>второй приоритетной</b> вакансии:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="departments_2",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_department_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.select_department_2,
        getter=get_departments_list,
    ),
    
    # Выбор позиции для второго приоритета
    Window(
        Format("👨‍💼 Выберите позицию в департаменте <b>{selected_department}</b>:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="positions_2",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_position_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад к департаментам")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.select_position_2,
        getter=get_positions_for_department,
    ),
    
    # Выбор департамента для третьего приоритета
    Window(
        Const("🏢 Выберите департамент для вашей <b>третьей приоритетной</b> вакансии:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="departments_3",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_department_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.select_department_3,
        getter=get_departments_list,
    ),
    
    # Выбор позиции для третьего приоритета
    Window(
        Format("👨‍💼 Выберите позицию в департаменте <b>{selected_department}</b>:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="positions_3",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_position_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад к департаментам")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.select_position_3,
        getter=get_positions_for_department,
    ),
    
    # Обзор всех приоритетов с возможностью редактирования
    Window(
        Const("📋 <b>Ваши приоритеты вакансий:</b>\n"),
        Format("{priorities_text}"),
        Format("\n💡 <i>Вы можете отредактировать любой приоритет, добавить новые или поменять их местами</i>"),
        Row(
            Button(Const("✅ Подтвердить выбор"), 
                   id="confirm_priorities", 
                   on_click=on_priority_confirmed),
        ),
        Group(
            Button(Const("➕ Продолжить выбор"), 
                   id="add_2",
                   on_click=on_add_priority_2,
                   when="can_add_2"),
            Button(Const("➕ Продолжить выбор"), 
                   id="add_3",
                   on_click=on_add_priority_3,
                   when="can_add_3"),
            width=2,
        ),
        Row(
            Button(Const("✏️ 1-й приоритет"), 
                   id="edit_1", 
                   on_click=on_edit_priority_1),
            Button(Const("✏️ 2-й приоритет"), 
                   id="edit_2", 
                   on_click=on_edit_priority_2),
            Button(Const("✏️ 3-й приоритет"), 
                   id="edit_3", 
                   on_click=on_edit_priority_3),
        ),
        Row(
            Button(Const("🔄 Поменять местами"), 
                   id="swap_priorities", 
                   on_click=on_swap_priorities),
            Button(Const("🆕 Начать заново"), 
                   id="start_over", 
                   on_click=on_start_over),
        ),
        Cancel(Const("❌ Отмена"), result="cancel"),
        state=JobSelectionSG.priorities_overview,
        getter=get_priorities_overview,
    ),
    
    # Редактирование 1-го приоритета - выбор департамента
    Window(
        Const("🏢 Редактирование <b>первого приоритета</b>\nВыберите новый департамент:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_department_selected,
            ),
        ),
        Row(
            Button(Const("⬅️ Назад к обзору"), 
                   id="back_to_overview", 
                   on_click=on_back_to_priorities_overview),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.edit_priority_1,
        getter=get_edit_departments_list,
    ),
    
    # Редактирование 1-го приоритета - выбор позиции
    Window(
        Format("👨‍💼 Редактирование <b>первого приоритета</b>\nВыберите позицию в департаменте <b>{selected_department}</b>:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_position_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад к департаментам")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.edit_priority_1_position,
        getter=get_edit_positions_for_department,
    ),
    
    # Редактирование 2-го приоритета - выбор департамента
    Window(
        Const("🏢 Редактирование <b>второго приоритета</b>\nВыберите новый департамент:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_department_selected,
            ),
        ),
        Row(
            Button(Const("⬅️ Назад к обзору"), 
                   id="back_to_overview_2", 
                   on_click=on_back_to_priorities_overview),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.edit_priority_2,
        getter=get_edit_departments_list,
    ),
    
    # Редактирование 2-го приоритета - выбор позиции
    Window(
        Format("👨‍💼 Редактирование <b>второго приоритета</b>\nВыберите позицию в департаменте <b>{selected_department}</b>:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_position_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад к департаментам")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.edit_priority_2_position,
        getter=get_edit_positions_for_department,
    ),
    
    # Редактирование 3-го приоритета - выбор департамента
    Window(
        Const("🏢 Редактирование <b>третьего приоритета</b>\nВыберите новый департамент:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_department_selected,
            ),
        ),
        Row(
            Button(Const("⬅️ Назад к обзору"), 
                   id="back_to_overview_3", 
                   on_click=on_back_to_priorities_overview),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.edit_priority_3,
        getter=get_edit_departments_list,
    ),
    
    # Редактирование 3-го приоритета - выбор позиции
    Window(
        Format("👨‍💼 Редактирование <b>третьего приоритета</b>\nВыберите позицию в департаменте <b>{selected_department}</b>:"),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_position_selected,
            ),
        ),
        Row(
            Back(Const("⬅️ Назад к департаментам")),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.edit_priority_3_position,
        getter=get_edit_positions_for_department,
    ),
    
    # Окно выбора типа обмена приоритетов
    Window(
        Const("🔄 <b>Выберите какие приоритеты поменять местами:</b>\n"),
        Const("💡 <i>Выберите пару приоритетов для обмена</i>"),
        Row(
            Button(Const("1️⃣↔️2️⃣ 1-й ↔ 2-й"), 
                   id="swap_1_2", 
                   on_click=on_swap_1_2),
            Button(Const("1️⃣↔️3️⃣ 1-й ↔ 3-й"), 
                   id="swap_1_3", 
                   on_click=on_swap_1_3),
        ),
        Row(
            Button(Const("2️⃣↔️3️⃣ 2-й ↔ 3-й"), 
                   id="swap_2_3", 
                   on_click=on_swap_2_3),
        ),
        Row(
            Button(Const("⬅️ Назад к обзору"), 
                   id="back_to_overview", 
                   on_click=on_back_to_priorities_overview),
            Cancel(Const("❌ Отмена"), result="cancel"),
        ),
        state=JobSelectionSG.swap_priorities_menu,
    ),
)
