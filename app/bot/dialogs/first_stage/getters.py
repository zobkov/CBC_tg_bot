import logging
from typing import Dict, Any

from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType

from config.config import Config
from app.infrastructure.database.database.db import DB
from app.utils.optimized_dialog_widgets import get_file_id_for_path

logger = logging.getLogger(__name__)


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
        if db and event_from_user:
            # Убедимся, что строка application существует
            await db.applications.create_application(user_id=event_from_user.id)
            # Читаем статус из users
            user_rec = await db.users.get_user_record(user_id=event_from_user.id)
            if user_rec and getattr(user_rec, 'submission_status', 'not_submitted') == 'submitted':
                can_apply = False
                application_status_text = "✅ Заявка отправлена"
            else:
                can_apply = True
                application_status_text = "⏳ Заявка не отправлена"
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
    checked_items = []
    
    if multiselect:
        checked_items = multiselect.get_checked()
        has_selections = len(checked_items) > 0
        was_in_kbk = "6" in checked_items  # Индекс опции "Ранее участвовал в КБК (2024-2025)"
        logger.info(f"📢 get_how_found_options: multiselect found, checked_items: {checked_items}")
    else:
        # Попробуем получить из dialog_data (для Redis)
        saved_selections = dialog_manager.dialog_data.get("how_found_selections", [])
        if saved_selections:
            checked_items = list(saved_selections)
            has_selections = len(checked_items) > 0
            was_in_kbk = "6" in checked_items
            logger.info(f"📢 get_how_found_options: используем сохраненные выборы: {checked_items}")
        else:
            logger.info(f"📢 get_how_found_options: multiselect не найден и нет сохраненных выборов")
    
    logger.info(f"📢 get_how_found_options результат: has_selections={has_selections}, was_in_kbk={was_in_kbk}")
    
    return {
        "how_found_options": options,
        "has_selections": has_selections,
        "was_in_kbk": was_in_kbk
    }


async def get_departments_for_previous(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем список департаментов для выбора предыдущего участия (legacy-список)."""
    # Legacy список отделов (id -> display text). Используем короткие ASCII id, чтобы не превысить лимит Telegram callback_data
    legacy_departments_map = {
        "legacy_program": "Отдел программы",
        "legacy_creative": "Творческий отдел",
        "legacy_partners": "Отдел партнёров",
        "legacy_smm_pr": "SMM&PR",
        "legacy_design": "Отдел дизайна",
        "legacy_logistics_it": "Логистика и ИТ",
        "legacy_cultural": "Культурно-экспертный отдел",
        "legacy_volunteer": "Волонтёр",
    }

    # Формируем элементы для Radio
    departments = [
        {"id": key, "text": title, "description": ""}
        for key, title in legacy_departments_map.items()
    ]

    # Проверяем, выбрал ли пользователь "Ранее участвовал в КБК" через Multiselect
    multiselect = dialog_manager.find("how_found_multiselect")
    was_in_kbk = False

    if multiselect:
        checked_items = multiselect.get_checked()
        was_in_kbk = "6" in checked_items  # Индекс опции "Ранее участвовал в КБК (2024-2025)"

    return {
        "departments": departments,
        "was_in_kbk": was_in_kbk,
        "departments_description": ""
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
    # Сначала пытаемся получить из dialog_data (где сохраняются данные при редактировании)
    how_found_selections = dialog_data.get("how_found_selections", [])
    
    # Если данных нет в dialog_data, пробуем получить из активного виджета
    if not how_found_selections:
        multiselect = dialog_manager.find("how_found_multiselect")
        if multiselect:
            how_found_selections = list(multiselect.get_checked())
    
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
        previous_dept_name = dialog_data.get("previous_department_name")
        if previous_dept_key or previous_dept_name:
            # Приоритетно используем сохраненное имя (для legacy)
            dept_name = previous_dept_name or config.selection.departments.get(previous_dept_key, {}).get("name", previous_dept_key)
            previous_dept_text = f"\n🏢 <b>Предыдущий отдел в КБК:</b> {dept_name}"
        # Если выбрано "Ранее участвовал в КБК", но отдел не указан, не показываем поле
    # Если не выбрано "Ранее участвовал в КБК", поле не показываем вообще
    
    # Формируем информацию о приоритетах вакансий
    priorities_summary = ""
    priorities_exist = False
    
    # Получаем данные переданные через start_data (например, от диалога выбора вакансий)
    start_data = dialog_manager.start_data or {}
    
    # Объединяем данные: приоритет у dialog_data, но start_data может дополнить
    combined_data = {**start_data, **dialog_data}
    
    for i in range(1, 4):
        # Используем combined_data для получения приоритетов
        dept_key = combined_data.get(f"priority_{i}_department")
        subdept_key = combined_data.get(f"priority_{i}_subdepartment")
        pos_index = combined_data.get(f"priority_{i}_position")
        
        print(f"DEBUG: get_form_summary - priority_{i}: dept='{dept_key}', subdept='{subdept_key}', pos='{pos_index}'")
        
        if dept_key and pos_index is not None:
            priorities_exist = True
            dept_data = config.selection.departments.get(dept_key, {})
            dept_name = dept_data.get("name", dept_key)
            
            # Если есть под-отдел, используем его позиции
            if subdept_key and "subdepartments" in dept_data:
                subdept_data = dept_data["subdepartments"].get(subdept_key, {})
                subdept_name = subdept_data.get("name", subdept_key)
                positions_list = subdept_data.get("positions", [])
                dept_display_name = f"{dept_name} – {subdept_name}"
            else:
                # Используем позиции основного отдела
                positions_list = dept_data.get("positions", [])
                dept_display_name = dept_name
            
            # Получаем позицию по индексу из массива
            try:
                pos_name = positions_list[int(pos_index)]
            except (IndexError, ValueError):
                pos_name = "Неизвестная позиция"
                
            priorities_summary += f"{i}. {dept_display_name} - {pos_name}\n"
        else:
            priorities_summary += f"{i}. Не выбрано\n"
    
    if not priorities_exist:
        priorities_summary = "❌ Вакансии не выбраны"
    
    print(f"DEBUG: get_form_summary - final priorities_summary = '{priorities_summary}'")
    
    course = dialog_data.get("course", "1")
    
    # Определяем статус резюме
    if "resume_file" in dialog_data:
        resume_filename = dialog_data.get("resume_file", "")
        resume_status = f"✅ Загружено: {resume_filename}"
    else:
        resume_status = "❌ Не загружено"
    
    # Получаем исходные данные
    experience = dialog_data.get("experience", "")
    motivation = dialog_data.get("motivation", "")
    
    print(f"DEBUG: get_form_summary - original experience length: {len(experience)}")
    print(f"DEBUG: get_form_summary - original motivation length: {len(motivation)}")
    
    # Усекаем длинные поля с умными ограничениями
    def truncate_text(text: str, max_length: int) -> str:
        """Усекает текст с добавлением троеточия если он превышает лимит"""
        if len(text) <= max_length:
            return text
        # Пытаемся обрезать по последнему пробелу, чтобы не разрывать слова
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # Если пробел найден не слишком далеко от конца
            truncated = truncated[:last_space]
        return truncated + "..."
    
    # Предварительные лимиты для полей (будут скорректированы ниже)
    experience_limit = 800
    motivation_limit = 800
    
    # Усекаем поля
    experience_truncated = truncate_text(experience, experience_limit)
    motivation_truncated = truncate_text(motivation, motivation_limit)
    
    # Создаем предварительную структуру данных
    summary_data = {
        "full_name": dialog_data.get("full_name", ""),
        "university": dialog_data.get("university", ""),
        "course_text": f"{course} курс",
        "phone": dialog_data.get("phone", ""),
        "email": dialog_data.get("email", ""),
        "how_found_text": how_found_text,
        "previous_dept_text": previous_dept_text,
        "priorities_summary": priorities_summary,
        "experience": experience_truncated,
        "motivation": motivation_truncated,
        "resume_status": resume_status
    }
    
    # Проверяем общую длину сообщения
    template = ("✅ <b>Проверь, что все данные заполнены верно. Если что-то нужно исправить — выбери пункт, в котором допустил ошибку, и обнови ответ.</b>\n\n"
               "👤 <b>ФИО:</b> {full_name}\n"
               "🏫 <b>Учебное заведение:</b> {university}\n"
               "📱 <b>Телефон:</b> {phone}\n"
               "📧 <b>Email:</b> {email}\n"
               "📢 <b>Откуда узнали:</b> {how_found_text}{previous_dept_text}\n"
               "💼 <b>Опыт:</b> {experience}\n"
               "💭 <b>Мотивация:</b> {motivation}\n"
               "📄 <b>Резюме:</b> {resume_status}\n"
               "\n<b>Приоритеты вакансий:</b>\n{priorities_summary}")
    
    # Формируем сообщение для проверки длины
    test_message = template.format(**summary_data)
    
    print(f"DEBUG: get_form_summary - initial message length: {len(test_message)}")
    
    # Telegram лимит 4096 символов, оставляем небольшой запас
    max_telegram_length = 4000
    
    # Если сообщение слишком длинное, дополнительно сокращаем динамические поля
    if len(test_message) > max_telegram_length:
        print(f"DEBUG: get_form_summary - message too long, applying additional truncation")
        # Рассчитываем избыточную длину
        excess_length = len(test_message) - max_telegram_length
        
        # Сокращаем experience и motivation пропорционально их размеру
        total_dynamic_length = len(experience_truncated) + len(motivation_truncated)
        
        if total_dynamic_length > 0:
            # Распределяем сокращение пропорционально
            exp_reduction = int(excess_length * len(experience_truncated) / total_dynamic_length)
            mot_reduction = excess_length - exp_reduction
            
            # Применяем дополнительное сокращение
            new_exp_limit = max(100, len(experience_truncated) - exp_reduction)
            new_mot_limit = max(100, len(motivation_truncated) - mot_reduction)
            
            print(f"DEBUG: get_form_summary - reducing experience to {new_exp_limit}, motivation to {new_mot_limit}")
            
            summary_data["experience"] = truncate_text(experience, new_exp_limit)
            summary_data["motivation"] = truncate_text(motivation, new_mot_limit)
            
            # Проверяем финальную длину
            final_message = template.format(**summary_data)
            print(f"DEBUG: get_form_summary - final message length: {len(final_message)}")
    
    print(f"DEBUG: get_form_summary - final experience length: {len(summary_data['experience'])}")
    print(f"DEBUG: get_form_summary - final motivation length: {len(summary_data['motivation'])}")
    
    return summary_data


async def get_edit_menu_data(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем данные для меню редактирования"""
    dialog_data = dialog_manager.dialog_data
    
    # Проверяем, участвовал ли пользователь в КБК (для показа кнопки редактирования предыдущего отдела)
    selected_options = dialog_data.get("how_found_selections", [])
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
    selected_options = dialog_data.get("how_found_selections", [])
    has_selections = len(selected_options) > 0
    
    return {
        "how_found_options": options,
        "has_selections": has_selections
    }


async def get_first_stage_media(dialog_manager: DialogManager, **kwargs):
    """Получаем медиа для первого окна first_stage"""
    file_id = get_file_id_for_path("first_stage_intro/Анкетирование.png")
    
    if file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path="app/bot/assets/images/first_stage_intro/Анкетирование.png"
        )
    
    return {
        "media": media
    }
