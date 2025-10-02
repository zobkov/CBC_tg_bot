from datetime import datetime
from typing import Dict, Any

from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType

from config.config import Config
from app.infrastructure.database.database.db import DB
from app.utils.optimized_dialog_widgets import get_file_id_for_path


async def get_user_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о пользователе"""
    
    return {
        "user_id": event_from_user.id,
        "username": event_from_user.username or "",
        "first_name": event_from_user.first_name or "",
        "last_name": event_from_user.last_name or "",
    }


async def get_current_stage_info(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о текущем этапе отбора"""
    from app.utils.deadline_checker import is_task_submission_closed, format_results_date
    
    config: Config = dialog_manager.middleware_data.get("config")
    db: DB = dialog_manager.middleware_data.get("db")
    event_from_user: User = dialog_manager.event.from_user
    
    if not config:
        return {
            "current_stage": "Неизвестно",
            "current_stage_description": "Информация недоступна",
            "is_active": False
        }
    
    # Получаем статус заявки пользователя из таблицы users (submission_status)
    application_submitted = False
    try:
        if db:
            user_record = await db.users.get_user_record(user_id=event_from_user.id)
            application_submitted = bool(user_record and user_record.submission_status == "submitted")
    except Exception:
        application_submitted = False
    
    # Проверяем, закрыта ли отправка тестовых заданий
    submission_closed = is_task_submission_closed()
    
    now = datetime.now()
    current_stage = None
    current_stage_info = None
    next_stage_info = None
    
    # Сортируем этапы по дате начала
    sorted_stages = sorted(
        config.selection.stages.items(),
        key=lambda x: datetime.fromisoformat(x[1]["start_date"])
    )
    
    # Находим текущий этап
    for i, (stage_key, stage_data) in enumerate(sorted_stages):
        start_date = datetime.fromisoformat(stage_data["start_date"])
        end_date = datetime.fromisoformat(stage_data["end_date"])
        
        if start_date <= now <= end_date:
            current_stage = stage_key
            current_stage_info = stage_data
            # Находим следующий этап
            if i + 1 < len(sorted_stages):
                next_stage_info = sorted_stages[i + 1][1]
            break
    
    if not current_stage:
        # Проверяем будущие этапы
        for stage_key, stage_data in sorted_stages:
            start_date = datetime.fromisoformat(stage_data["start_date"])
            if now < start_date:
                current_stage = stage_key
                current_stage_info = stage_data
                current_stage_info["status"] = "upcoming"
                break
    
    if not current_stage_info:
        current_stage_info = {
            "name": "Отбор завершен",
            "description": "Все этапы отбора завершены",
            "status": "completed"
        }
    
    # Логика отображения дедлайна и результатов
    deadline_info = ""
    
    # Если отправка тестовых заданий закрыта, переопределяем информацию о этапе
    if submission_closed:
        current_stage_info = {
            "name": "Тестовое задание",
            "description": "",
            "status": "closed"
        }
        
        # Формируем информацию о результатах
        results_date = format_results_date()
        deadline_info = f"\n\n⏰ <b>Результаты:</b> {results_date}"
    else:
        # Если дедлайн еще не прошел, показываем дедлайн (для этапа "Тестовое задание")
        if current_stage_info and current_stage_info.get("name") == "Тестовое задание":
            deadline_info = f"\n\n⏰ <b>Дедлайн:</b> 02.10.2025, 23:59"
    
    # Добавляем информацию о следующем этапе
    next_stage_text = ""
    #if next_stage_info and current_stage_info.get("status") != "upcoming":
     #   next_start = datetime.fromisoformat(next_stage_info["start_date"])
    #    next_stage_text = f"\n\n📋 <b>Следующий этап:</b> {next_stage_info['name']}\n🚀 <b>Начало:</b> {next_start.strftime('%d.%m.%Y, %H:%M')}"
    
    return {
        "current_stage": current_stage or "completed",
        "stage_name": current_stage_info["name"],
        "stage_description": current_stage_info.get("description", "") + next_stage_text,
        "stage_status": current_stage_info.get("status", "active"),
        "deadline_info": deadline_info,
        "submission_closed": submission_closed
    }


async def get_application_status(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем статус заявки пользователя"""
    event_from_user: User = dialog_manager.event.from_user
    
    # Получаем объект DB из middleware_data
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        return {
            "application_status": "not_submitted",
            "status_text": "Заявка не подана",
            "can_apply": True
        }
    
    try:
        # Ensure application row exists for form fields (no status stored here)
        await db.applications.create_application(user_id=event_from_user.id)
        user_record = await db.users.get_user_record(user_id=event_from_user.id)
        application_status = (user_record.submission_status if user_record else "not_submitted")
        status_text = {
            "not_submitted": "Заявка не подана",
            "submitted": "Заявка подана"
        }.get(application_status, "Неизвестный статус")
    except Exception as e:
        # В случае ошибки возвращаем значения по умолчанию
        application_status = "not_submitted"
        status_text = "Заявка не подана"
    
    return {
        "application_status": application_status,
        "status_text": status_text,
        "can_apply": application_status == "not_submitted"
    }


async def get_support_contacts(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем контакты поддержки"""
    config: Config = dialog_manager.middleware_data.get("config")
    
    if not config:
        return {
            "general_support": "Недоступно",
            "technical_support": "Недоступно",
            "hr_support": "Недоступно"
        }
    
    return {
        "general_support": config.selection.support_contacts["general"],
        "technical_support": config.selection.support_contacts["technical"],
        "hr_support": config.selection.support_contacts["hr"]
    }


async def get_task_button_info(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем информацию для кнопки тестовых заданий"""
    from app.utils.deadline_checker import is_task_submission_closed
    
    event_from_user: User = dialog_manager.event.from_user
    db: DB = dialog_manager.middleware_data.get("db")
    
    # Проверяем, закрыта ли отправка тестовых заданий
    submission_closed = is_task_submission_closed()
    
    # По умолчанию доступ разрешен (для случаев ошибок или отсутствия данных)
    is_first_stage_passed = True
    button_emoji = "📋"
    
    if submission_closed:
        # Если дедлайн прошел, показываем замочек независимо от статуса
        button_emoji = "🔒"
    elif db:
        try:
            # Получаем данные оценки пользователя
            evaluation = await db.evaluated_applications.get_evaluation(user_id=event_from_user.id)
            
            if evaluation:
                # Проверяем, прошел ли пользователь первый этап
                # Если все accepted_1, accepted_2, accepted_3 = False, значит не прошел
                is_first_stage_passed = evaluation.accepted_1 or evaluation.accepted_2 or evaluation.accepted_3
                
                if not is_first_stage_passed:
                    button_emoji = "🔒"
            else:
                # Если пользователя нет в evaluated_applications, значит он не отправлял заявку
                button_emoji = "🔒"
                is_first_stage_passed = False
        except Exception as e:
            # В случае ошибки логируем и разрешаем доступ
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking first stage status for user {event_from_user.id}: {e}")
    
    return {
        "task_button_emoji": button_emoji,
        "is_first_stage_passed": is_first_stage_passed,
        "submission_closed": submission_closed
    }


async def get_task_status_info(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о статусе выполнения тестовых заданий"""
    event_from_user: User = dialog_manager.event.from_user
    db: DB = dialog_manager.middleware_data.get("db")
    
    task_status_text = "Решения не получены"
    
    if db:
        try:
            # Получаем данные о пользователе и оценке
            user_record = await db.users.get_user_record(user_id=event_from_user.id)
            evaluation = await db.evaluated_applications.get_evaluation(user_id=event_from_user.id)
            
            if user_record and evaluation:
                # Проверяем, по каким заданиям пользователь был принят и отправил ли решения
                submitted_tasks = []
                
                if evaluation.accepted_1 and user_record.task_1_submitted:
                    submitted_tasks.append("1")
                elif evaluation.accepted_1:
                    # Принят, но не отправил
                    pass
                    
                if evaluation.accepted_2 and user_record.task_2_submitted:
                    submitted_tasks.append("2")
                elif evaluation.accepted_2:
                    # Принят, но не отправил
                    pass
                    
                if evaluation.accepted_3 and user_record.task_3_submitted:
                    submitted_tasks.append("3")
                elif evaluation.accepted_3:
                    # Принят, но не отправил
                    pass
                
                # Если есть отправленные задания, формируем соответствующий текст
                if submitted_tasks:
                    task_status_text = "Решения получены"
                else:
                    # Проверяем, был ли принят хотя бы по одному заданию
                    accepted_any = evaluation.accepted_1 or evaluation.accepted_2 or evaluation.accepted_3
                    if accepted_any:
                        task_status_text = "Решения не получены"
                    else:
                        # Не принят ни по одному заданию
                        task_status_text = "Решения не получены"
            
        except Exception as e:
            # В случае ошибки возвращаем значение по умолчанию
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting task status for user {event_from_user.id}: {e}")
    
    return {
        "task_status_text": task_status_text
    }


async def get_main_menu_media(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получаем медиа для главного меню"""
    file_id = get_file_id_for_path("main_menu/main_menu.jpg")
    
    if file_id:
        # Используем file_id для быстрой отправки
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(file_id)
        )
    else:
        # Fallback на путь к файлу
        media = MediaAttachment(
            type=ContentType.PHOTO,
            path="app/bot/assets/images/main_menu/main_menu.jpg"
        )
    
    return {
        "media": media
    }
