from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Select, Row, Back, Next, Start, Button, Column, Group, SwitchTo
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.media import StaticMedia, DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from aiogram.enums import ContentType

from app.bot.states.job_selection import JobSelectionSG
from app.bot.states.first_stage import FirstStageSG
from .getters import (
    get_departments_list, get_subdepartments_list, get_positions_for_department, get_priorities_overview,
    get_edit_departments_list, get_edit_subdepartments_list, get_edit_positions_for_department
)
from .handlers import (
    on_department_selected, on_subdepartment_selected, on_position_selected, on_priority_confirmed,
    on_edit_priority_1, on_edit_priority_2, on_edit_priority_3,
    on_swap_priorities, on_edit_department_selected, on_edit_subdepartment_selected, on_edit_position_selected,
    on_swap_1_2, on_swap_1_3, on_swap_2_3, on_back_to_priorities_overview,
    on_add_priority_2, on_add_priority_3
)

job_selection_dialog = Dialog(
    # Выбор департамента для первого приоритета
    Window(
        StaticMedia(
           path="app/bot/dialogs/job_selection/assets/1.jpeg"
        ),
        Const(
            "Работа КБК — это синергия 7 разных отделов, каждый из которых одинаково важен! \n"
            "Выбери тот, который привлекает тебя больше всего. Подробнее о каждом отделе — в карточках ниже\n\n"
            "Выберите отдел для твоей <b>первой приоритетной</b> вакансии:"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_department_selected,
            ),
        ),
        state=JobSelectionSG.select_department,
        getter=get_departments_list,
    ),
    
    # Выбор под-отдела для первого приоритета
    Window(
        Format("🏢 <b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("Выберите направление в данном отделе:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="subdepartments",
                items="subdepartments",
                item_id_getter=lambda item: item[0],
                on_click=on_subdepartment_selected,
            ),
        ),
        Back(Const("⬅️ Назад к отделам")),
        state=JobSelectionSG.select_subdepartment,
        getter=get_subdepartments_list,
    ),
    
    # Выбор позиции для первого приоритета
    Window(
        Format("👨‍💼 <b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("Выберите позицию:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_position_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id='back_to_dep_1', state=JobSelectionSG.select_department),
        state=JobSelectionSG.select_position,
        getter=get_positions_for_department,
    ),
    
    # Выбор департамента для второго приоритета
    Window(
        Const("🏢 Выберите отдел для вашей <b>второй приоритетной</b> вакансии:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="departments_2",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_department_selected,
            ),
        ),
        Back(Const("⬅️ Назад")),
        state=JobSelectionSG.select_department_2,
        getter=get_departments_list,
    ),
    
    # Выбор под-отдела для второго приоритета
    Window(
        Format("🏢 <b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("Выберите направление в данном отделе:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="subdepartments_2",
                items="subdepartments",
                item_id_getter=lambda item: item[0],
                on_click=on_subdepartment_selected,
            ),
        ),
        Back(Const("⬅️ Назад к отделам")),
        state=JobSelectionSG.select_subdepartment_2,
        getter=get_subdepartments_list,
    ),
    
    # Выбор позиции для второго приоритета
    Window(
        Format("👨‍💼 <b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("Выберите позицию:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="positions_2",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_position_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id='back_to_dep_1', state=JobSelectionSG.select_department_2),
        state=JobSelectionSG.select_position_2,
        getter=get_positions_for_department,
    ),
    
    # Выбор департамента для третьего приоритета
    Window(
        Const("🏢 Выберите отдел для вашей <b>третьей приоритетной</b> вакансии:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="departments_3",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_department_selected,
            ),
        ),
        Back(Const("⬅️ Назад")),
        state=JobSelectionSG.select_department_3,
        getter=get_departments_list,
    ),
    
    # Выбор под-отдела для третьего приоритета
    Window(
        Format("🏢 <b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("Выберите направление в данном отделе:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="subdepartments_3",
                items="subdepartments",
                item_id_getter=lambda item: item[0],
                on_click=on_subdepartment_selected,
            ),
        ),
        Back(Const("⬅️ Назад к отделам")),
        state=JobSelectionSG.select_subdepartment_3,
        getter=get_subdepartments_list,
    ),
    
    # Выбор позиции для третьего приоритета
    Window(
        Format("👨‍💼 <b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("Выберите позицию:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="positions_3",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_position_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id='back_to_dep_1', state=JobSelectionSG.select_department_3),
        state=JobSelectionSG.select_position_3,
        getter=get_positions_for_department,
    ),
    
    # Обзор всех приоритетов с возможностью редактирования
    Window(
        Const("📋 <b>Ваши приоритеты вакансий:</b>\n"),
        Format("{priorities_text}"),
        Format("\n💡 <i>Вы можете отредактировать любой приоритет, добавить новые или поменять их местами</i>"),
        Row(
            Button(Const("✅ Продолжить заполнение анкеты"), 
                   id="confirm_priorities", 
                   on_click=on_priority_confirmed),
        ),
        Row(
            Button(Const("✏️ 1-й"), 
                   id="edit_1", 
                   on_click=on_edit_priority_1),
            Button(Const("✏️ 2-й"), 
                   id="edit_2", 
                   on_click=on_edit_priority_2),
            Button(Const("✏️ 3-й"), 
                   id="edit_3", 
                   on_click=on_edit_priority_3),
        ),
        Row(
            Button(Const("🔄 Поменять местами"), 
                   id="swap_priorities", 
                   on_click=on_swap_priorities),
        ),
        state=JobSelectionSG.priorities_overview,
        getter=get_priorities_overview,
    ),
    
    # Редактирование 1-го приоритета - выбор департамента
    Window(
        Const("🏢 Редактирование <b>первого приоритета</b>\nВыберите новый отдел:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_department_selected,
            ),
        ),
        Button(Const("⬅️ Назад к обзору"), 
               id="back_to_overview", 
               on_click=on_back_to_priorities_overview),
        state=JobSelectionSG.edit_priority_1,
        getter=get_edit_departments_list,
    ),
    
    # Редактирование 1-го приоритета - выбор под-отдела
    Window(
        Format("🏢 Редактирование <b>первого приоритета</b>\n<b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("<b>Выберите направление в данном отделе:</b>"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_subdepartments",
                items="subdepartments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_subdepartment_selected,
            ),
        ),
        Back(Const("⬅️ Назад к отделам")),
        state=JobSelectionSG.edit_priority_1_subdepartment,
        getter=get_edit_subdepartments_list,
    ),
    
    # Редактирование 1-го приоритета - выбор позиции
    Window(
        Format("👨‍💼 Редактирование <b>первого приоритета</b>\n<b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("<b>Выберите позицию:</b>"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_position_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id='edit_back_to_dep_1', state=JobSelectionSG.edit_priority_1),
        state=JobSelectionSG.edit_priority_1_position,
        getter=get_edit_positions_for_department,
    ),
    
    # Редактирование 2-го приоритета - выбор департамента
    Window(
        Const("🏢 Редактирование <b>второго приоритета</b>\nВыберите новый отдел:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_department_selected,
            ),
        ),
        Button(Const("⬅️ Назад к обзору"), 
               id="back_to_overview_2", 
               on_click=on_back_to_priorities_overview),
        state=JobSelectionSG.edit_priority_2,
        getter=get_edit_departments_list,
    ),
    
    # Редактирование 2-го приоритета - выбор под-отдела
    Window(
        Format("🏢 Редактирование <b>второго приоритета</b>\n<b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("<b>Выберите направление в данном отделе:</b>"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_subdepartments",
                items="subdepartments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_subdepartment_selected,
            ),
        ),
        Back(Const("⬅️ Назад к отделам")),
        state=JobSelectionSG.edit_priority_2_subdepartment,
        getter=get_edit_subdepartments_list,
    ),
    
    # Редактирование 2-го приоритета - выбор позиции
    Window(
        Format("👨‍💼 Редактирование <b>второго приоритета</b>\n<b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("<b>Выберите позицию:</b>"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_position_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id='edit_back_to_dep_2', state=JobSelectionSG.edit_priority_2),
        state=JobSelectionSG.edit_priority_2_position,
        getter=get_edit_positions_for_department,
    ),
    
    # Редактирование 3-го приоритета - выбор департамента
    Window(
        Const("🏢 Редактирование <b>третьего приоритета</b>\nВыберите новый отдел:"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_departments",
                items="departments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_department_selected,
            ),
        ),
        Button(Const("⬅️ Назад к обзору"), 
               id="back_to_overview_3", 
               on_click=on_back_to_priorities_overview),
        state=JobSelectionSG.edit_priority_3,
        getter=get_edit_departments_list,
    ),
    
    # Редактирование 3-го приоритета - выбор под-отдела
    Window(
        Format("🏢 Редактирование <b>третьего приоритета</b>\n<b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("<b>Выберите направление в данном отделе:</b>"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_subdepartments",
                items="subdepartments",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_subdepartment_selected,
            ),
        ),
        Back(Const("⬅️ Назад к отделам")),
        state=JobSelectionSG.edit_priority_3_subdepartment,
        getter=get_edit_subdepartments_list,
    ),
    
    # Редактирование 3-го приоритета - выбор позиции
    Window(
        Format("👨‍💼 Редактирование <b>третьего приоритета</b>\n<b>{selected_department}</b>\n\n{department_description}\n\n"),
        Format("<b>Выберите позицию:</b>"),
        StaticMedia(
            path="app/bot/dialogs/job_selection/assets/1.jpeg",
            type="photo"
        ),
        Column(
            Select(
                Format("{item[1]}"),
                id="edit_positions",
                items="positions",
                item_id_getter=lambda item: item[0],
                on_click=on_edit_position_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id='edit_back_to_dep_3', state=JobSelectionSG.edit_priority_3),
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
        Button(Const("⬅️ Назад к обзору"), 
               id="back_to_overview", 
               on_click=on_back_to_priorities_overview),
        state=JobSelectionSG.swap_priorities_menu,
    ),
)
