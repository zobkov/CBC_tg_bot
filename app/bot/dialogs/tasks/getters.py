from datetime import datetime
from typing import Dict, Any
import logging

from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType

from config.config import Config
from app.infrastructure.database.database.db import DB
from app.utils.optimized_dialog_widgets import get_file_id_for_path
from app.utils.task_statistics import record_task_statistics

from app.infrastructure.database.models.applications import ApplicationsModel

logger = logging.getLogger(__name__)


async def get_live_tasks_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о принятии пользователя по заданиям"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        # Если БД недоступна, возвращаем дефолтные значения
        return {
            "task_1_is_live": False,
            "task_2_is_live": False,
            "task_3_is_live": False
        }
    
    try:
        # Получаем данные оценки пользователя из БД
        evaluation = await db.evaluated_applications.get_evaluation(user_id=event_from_user.id)
        
        if evaluation:
            return {
                "task_1_is_live": evaluation.accepted_1,
                "task_2_is_live": evaluation.accepted_2,
                "task_3_is_live": evaluation.accepted_3
            }
        else:
            # Если данных нет, возвращаем False для всех заданий
            return {
                "task_1_is_live": False,
                "task_2_is_live": False,
                "task_3_is_live": False
            }
    except Exception as e:
        # В случае ошибки логируем и возвращаем дефолтные значения
        logger.error(f"Error getting evaluation for user {event_from_user.id}: {e}")
        return {
            "task_1_is_live": False,
            "task_2_is_live": False,
            "task_3_is_live": False
        }

async def get_user_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о пользователе и записываем статистику посещения TaskSG.main"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    # Записываем статистику посещения TaskSG.main (только при первом заходе)
    if db:
        try:
            await record_task_statistics(db, event_from_user)
        except Exception as e:
            logger.error(f"Error recording task statistics for user {event_from_user.id}: {e}")
    
    return {
        "user_id": event_from_user.id,
        "username": event_from_user.username or "",
        "first_name": event_from_user.first_name or "",
        "last_name": event_from_user.last_name or "",
    }

async def get_task_1_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о первой вакансии пользователя"""

    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        # Если БД недоступна, возвращаем дефолтные значения
        logger.error("Database connection not available in get_task_1_info")
        return {
            "deparment_1": "",
            "subdepartment_1": "",
            "position_1": "",
            "task_1_header": "База данных недоступна"
        }

    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=event_from_user.id)
        
        if not application:
            logger.warning(f"No application found for user {event_from_user.id}")
            return {
                "deparment_1": "",
                "subdepartment_1": "",
                "position_1": "",
                "task_1_header": "Заявка не найдена"
            }

        return {
            "deparment_1": application.department_1 or "",
            "subdepartment_1": application.subdepartment_1 or "",
            "position_1": application.position_1 or "",
            "task_1_header": f"{application.department_1 or ''}" + 
                           (f" – {application.subdepartment_1}" if application.subdepartment_1 else "") + 
                           f" – {application.position_1 or ''}"
        }
        
    except Exception as e:
        logger.error(f"Error getting task 1 info for user {event_from_user.id}: {e}")
        return {
            "deparment_1": "",
            "subdepartment_1": "",
            "position_1": "",
            "task_1_header": "Ошибка загрузки"
        }

async def get_task_2_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о второй вакансии пользователя"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        # Если БД недоступна, возвращаем дефолтные значения
        logger.error("Database connection not available in get_task_2_info")
        return {
            "deparment_2": "",
            "subdepartment_2": "",
            "position_2": "",
            "task_2_header": "База данных недоступна"
        }

    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=event_from_user.id)
        
        if not application:
            logger.warning(f"No application found for user {event_from_user.id}")
            return {
                "deparment_2": "",
                "subdepartment_2": "",
                "position_2": "",
                "task_2_header": "Заявка не найдена"
            }

        return {
            "deparment_2": application.department_2 or "",
            "subdepartment_2": application.subdepartment_2 or "",
            "position_2": application.position_2 or "",
            "task_2_header": f"{application.department_2 or ''}" + 
                           (f" – {application.subdepartment_2}" if application.subdepartment_2 else "") + 
                           f" – {application.position_2 or ''}"
        }
        
    except Exception as e:
        logger.error(f"Error getting task 2 info for user {event_from_user.id}: {e}")
        return {
            "deparment_2": "",
            "subdepartment_2": "",
            "position_2": "",
            "task_2_header": "Ошибка загрузки"
        }

async def get_task_3_info(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о третьей вакансии пользователя"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        # Если БД недоступна, возвращаем дефолтные значения
        logger.error("Database connection not available in get_task_3_info")
        return {
            "deparment_3": "",
            "subdepartment_3": "",
            "position_3": "",
            "task_3_header": "База данных недоступна"
        }

    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=event_from_user.id)
        
        if not application:
            logger.warning(f"No application found for user {event_from_user.id}")
            return {
                "deparment_3": "",
                "subdepartment_3": "",
                "position_3": "",
                "task_3_header": "Заявка не найдена"
            }

        return {
            "deparment_3": application.department_3 or "",
            "subdepartment_3": application.subdepartment_3 or "",
            "position_3": application.position_3 or "",
            "task_3_header": f"{application.department_3 or ''}" + 
                           (f" – {application.subdepartment_3}" if application.subdepartment_3 else "") + 
                           f" – {application.position_3 or ''}"
        }
        
    except Exception as e:
        logger.error(f"Error getting task 3 info for user {event_from_user.id}: {e}")
        return {
            "deparment_3": "",
            "subdepartment_3": "",
            "position_3": "",
            "task_3_header": "Ошибка загрузки"
        }
    
async def get_tasks_files(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем файлы заданий для всех трех приоритетов пользователя в виде MediaAttachment объектов"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        logger.error("Database connection not available in get_tasks_files")
        return {
            "task_1": None,
            "task_2": None,
            "task_3": None,
        }

    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=event_from_user.id)
        
        if not application:
            logger.warning(f"No application found for user {event_from_user.id}")
            return {
                "task_1": None,
                "task_2": None,
                "task_3": None,
            }

        # Импортируем функции для получения файлов заданий
        from app.utils.position_mapping import get_task_file_for_position
        from app.utils.task_file_id import get_task_file_id
        
        # Получаем файлы для каждого приоритета
        task_1_media = None
        task_2_media = None
        task_3_media = None
        
        # Первый приоритет
        if application.department_1 and application.position_1:
            task_1_file = get_task_file_for_position(
                department=application.department_1,
                subdepartment=application.subdepartment_1,
                position=application.position_1
            )
            if task_1_file:
                file_id = get_task_file_id(task_1_file)
                if file_id:
                    task_1_media = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(file_id))
        
        # Второй приоритет
        if application.department_2 and application.position_2:
            task_2_file = get_task_file_for_position(
                department=application.department_2,
                subdepartment=application.subdepartment_2,
                position=application.position_2
            )
            if task_2_file:
                file_id = get_task_file_id(task_2_file)
                if file_id:
                    task_2_media = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(file_id))
                else:
                    logger.error(f"file_id не найден для task_2_file: '{task_2_file}' (пользователь {event_from_user.id})")
            else:
                logger.error(f"Файл задания не найден для приоритета 2: {application.department_2}/{application.subdepartment_2}/{application.position_2} (пользователь {event_from_user.id})")
        
        # Третий приоритет
        if application.department_3 and application.position_3:
            task_3_file = get_task_file_for_position(
                department=application.department_3,
                subdepartment=application.subdepartment_3,
                position=application.position_3
            )
            if task_3_file:
                file_id = get_task_file_id(task_3_file)
                if file_id:
                    task_3_media = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(file_id))

        logger.info(f"Task media files for user {event_from_user.id}: task_1={task_1_media is not None}, task_2={task_2_media is not None}, task_3={task_3_media is not None}")
        
        # Дополнительная диагностическая информация
        if not task_1_media and application.department_1 and application.position_1:
            logger.warning(f"Task 1 media missing for user {event_from_user.id}: {application.department_1}/{application.subdepartment_1}/{application.position_1}")
        if not task_2_media and application.department_2 and application.position_2:
            logger.warning(f"Task 2 media missing for user {event_from_user.id}: {application.department_2}/{application.subdepartment_2}/{application.position_2}")
        if not task_3_media and application.department_3 and application.position_3:
            logger.warning(f"Task 3 media missing for user {event_from_user.id}: {application.department_3}/{application.subdepartment_3}/{application.position_3}")

        return {
            "task_1": task_1_media,
            "task_2": task_2_media,
            "task_3": task_3_media,
        }
        
    except Exception as e:
        logger.error(f"Error getting task files for user {event_from_user.id}: {e}")
        return {
            "task_1": None,
            "task_2": None,
            "task_3": None,
        }


async def get_user_task_submission_status(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем статус отправки заданий пользователя"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        return {
            "task_1_submitted": False,
            "task_2_submitted": False,
            "task_3_submitted": False
        }

    try:
        # Получаем пользователя из БД
        user = await db.users.get_user_record(user_id=event_from_user.id)
        
        if user:
            return {
                "task_1_submitted": user.task_1_submitted if hasattr(user, 'task_1_submitted') else False,
                "task_2_submitted": user.task_2_submitted if hasattr(user, 'task_2_submitted') else False,
                "task_3_submitted": user.task_3_submitted if hasattr(user, 'task_3_submitted') else False
            }
        else:
            return {
                "task_1_submitted": False,
                "task_2_submitted": False,
                "task_3_submitted": False
            }
        
    except Exception as e:
        logger.error(f"Error getting user task submission status {event_from_user.id}: {e}")
        return {
            "task_1_submitted": False,
            "task_2_submitted": False,
            "task_3_submitted": False
        }


async def get_user_files_info_task_1(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о файлах пользователя для задания 1"""
    return await _get_user_files_info(dialog_manager, event_from_user, task_number=1)


async def get_user_files_info_task_2(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о файлах пользователя для задания 2"""
    return await _get_user_files_info(dialog_manager, event_from_user, task_number=2)


async def get_user_files_info_task_3(dialog_manager: DialogManager, event_from_user: User, **kwargs) -> Dict[str, Any]:
    """Получаем информацию о файлах пользователя для задания 3"""
    return await _get_user_files_info(dialog_manager, event_from_user, task_number=3)


async def _get_user_files_info(dialog_manager: DialogManager, event_from_user: User, task_number: int) -> Dict[str, Any]:
    """Вспомогательная функция для получения информации о файлах пользователя"""
    
    # Получаем доступ к базе данных из dialog_manager
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        return {
            "files_list": [],
            "files_count": 0,
            "files_text": "Файлы не загружены"
        }

    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=event_from_user.id)
        
        if not application:
            return {
                "files_list": [],
                "files_count": 0,
                "files_text": "Заявка не найдена"
            }

        # Определяем отдел для задания
        department = None
        if task_number == 1:
            department = application.department_1
        elif task_number == 2:
            department = application.department_2
        elif task_number == 3:
            department = application.department_3
        
        if not department:
            return {
                "files_list": [],
                "files_count": 0,
                "files_text": "Отдел не определен"
            }

        # Получаем список файлов
        from app.utils.user_files_manager import UserFilesManager
        files_manager = UserFilesManager()
        files_list = files_manager.get_user_files_list(
            user_id=event_from_user.id,
            task_number=task_number,
            department=department
        )
        
        # Формируем текст списка файлов
        if files_list:
            files_text_lines = []
            for file_info in files_list:
                files_text_lines.append(f"{file_info['number']}. {file_info['original_name']}")
            files_text = "\n".join(files_text_lines)
        else:
            files_text = "Файлы не загружены"

        return {
            "files_list": files_list,
            "files_count": len(files_list),
            "files_text": files_text
        }
        
    except Exception as e:
        logger.error(f"Error getting user files info for task {task_number}, user {event_from_user.id}: {e}")
        return {
            "files_list": [],
            "files_count": 0,
            "files_text": "Ошибка загрузки информации о файлах"
        }
    