import os
import logging
import asyncio
from typing import Dict, Set
from aiogram.types import Message, CallbackQuery, Document
from aiogram_dialog import DialogManager, ShowMode

from app.bot.states.first_stage import FirstStageSG
from app.bot.states.main_menu import MainMenuSG
from app.bot.states.tasks import TasksSG
from app.utils.user_files_manager import UserFilesManager
from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.applications import ApplicationsModel

logger = logging.getLogger(__name__)

# Глобальный словарь для отслеживания активных загрузок
# Структура: {user_id: {task_number: set_of_active_uploads}}
active_uploads: Dict[int, Dict[int, Set[str]]] = {}

# Максимальный размер файла в байтах (100 МБ)
MAX_FILE_SIZE = 100 * 1024 * 1024


def _add_active_upload(user_id: int, task_number: int, upload_id: str) -> None:
    """Добавляет активную загрузку для отслеживания"""
    if user_id not in active_uploads:
        active_uploads[user_id] = {}
    if task_number not in active_uploads[user_id]:
        active_uploads[user_id][task_number] = set()
    active_uploads[user_id][task_number].add(upload_id)


def _remove_active_upload(user_id: int, task_number: int, upload_id: str) -> bool:
    """Удаляет активную загрузку и возвращает True, если это была последняя активная загрузка"""
    if (user_id in active_uploads and 
        task_number in active_uploads[user_id] and 
        upload_id in active_uploads[user_id][task_number]):
        
        active_uploads[user_id][task_number].discard(upload_id)
        
        # Возвращаем True, если больше нет активных загрузок для этого задания
        return len(active_uploads[user_id][task_number]) == 0
    
    return True  # Если загрузки не было в списке, считаем что это последняя


def _get_active_uploads_count(user_id: int, task_number: int) -> int:
    """Возвращает количество активных загрузок для пользователя и задания"""
    if (user_id in active_uploads and 
        task_number in active_uploads[user_id]):
        return len(active_uploads[user_id][task_number])
    return 0

async def on_live_task_1_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовое задание 1'"""
    
    # Проверяем, не отправлено ли уже задание
    db: DB = dialog_manager.middleware_data.get("db")
    if db:
        try:
            user = await db.users.get_user_record(user_id=callback.from_user.id)
            if user and hasattr(user, 'task_1_submitted') and user.task_1_submitted:
                await dialog_manager.switch_to(state=TasksSG.task_1_submitted)
                return
        except Exception as e:
            logger.error(f"Error checking task 1 submission status: {e}")
    
    await dialog_manager.switch_to(state=TasksSG.task_1)


async def on_live_task_2_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовое задание 2'"""
    
    # Проверяем, не отправлено ли уже задание
    db: DB = dialog_manager.middleware_data.get("db")
    if db:
        try:
            user = await db.users.get_user_record(user_id=callback.from_user.id)
            if user and hasattr(user, 'task_2_submitted') and user.task_2_submitted:
                await dialog_manager.switch_to(state=TasksSG.task_2_submitted)
                return
        except Exception as e:
            logger.error(f"Error checking task 2 submission status: {e}")
    
    await dialog_manager.switch_to(state=TasksSG.task_2)


async def on_live_task_3_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовое задание 3'"""
    
    # Проверяем, не отправлено ли уже задание
    db: DB = dialog_manager.middleware_data.get("db")
    if db:
        try:
            user = await db.users.get_user_record(user_id=callback.from_user.id)
            if user and hasattr(user, 'task_3_submitted') and user.task_3_submitted:
                await dialog_manager.switch_to(state=TasksSG.task_3_submitted)
                return
        except Exception as e:
            logger.error(f"Error checking task 3 submission status: {e}")
    
    await dialog_manager.switch_to(state=TasksSG.task_3)


async def on_document_upload_task_1(message: Message, message_input, dialog_manager: DialogManager):
    """Обработчик загрузки документа для задания 1"""
    await _handle_document_upload(message, dialog_manager, task_number=1)


async def on_document_upload_task_2(message: Message, message_input, dialog_manager: DialogManager):
    """Обработчик загрузки документа для задания 2"""
    await _handle_document_upload(message, dialog_manager, task_number=2)


async def on_document_upload_task_3(message: Message, message_input, dialog_manager: DialogManager):
    """Обработчик загрузки документа для задания 3"""
    await _handle_document_upload(message, dialog_manager, task_number=3)


async def _handle_document_upload(message: Message, dialog_manager: DialogManager, task_number: int):
    """Общий обработчик загрузки документов"""
    
    if not message.document:
        await message.answer("❌ Пожалуйста, отправьте файл как документ")
        return

    document: Document = message.document
    
    # Проверяем размер файла
    if document.file_size > MAX_FILE_SIZE:
        await message.answer(f"❌ Размер файла превышает лимит в 100 МБ. Размер вашего файла: {document.file_size / 1024 / 1024:.1f} МБ")
        return
    
    # Создаем уникальный ID для этой загрузки
    upload_id = f"{message.message_id}_{document.file_id}"
    user_id = message.from_user.id
    
    # Добавляем загрузку в список активных
    _add_active_upload(user_id, task_number, upload_id)
    
    # Получаем доступ к базе данных и боту
    db: DB = dialog_manager.middleware_data.get("db")
    bot = dialog_manager.middleware_data.get("bot")
    
    if not db or not bot:
        await message.answer("❌ Ошибка системы, попробуйте позже")
        _remove_active_upload(user_id, task_number, upload_id)
        return
    
    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=user_id)
        
        if not application:
            await message.answer("❌ Заявка не найдена")
            _remove_active_upload(user_id, task_number, upload_id)
            return
        
        # Определяем отдел для задания
        department = None
        if task_number == 1:
            department = application.department_1
        elif task_number == 2:
            department = application.department_2
        elif task_number == 3:
            department = application.department_3
        
        if not department:
            await message.answer("❌ Отдел не определен для этого задания")
            _remove_active_upload(user_id, task_number, upload_id)
            return
        
        # Скачиваем файл
        file_info = await bot.get_file(document.file_id)
        
        # Создаем временную директорию для загрузки
        temp_dir = "storage/temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Временный путь для скачанного файла
        temp_file_path = os.path.join(temp_dir, f"temp_{user_id}_{document.file_id}")
        
        # Скачиваем файл
        await bot.download_file(file_info.file_path, temp_file_path)
        
        # Сохраняем файл через менеджер
        files_manager = UserFilesManager()
        
        full_name = application.full_name or f"User_{user_id}"
        username = message.from_user.username or "no_username"
        
        saved_file_path = files_manager.save_user_file(
            file_path=temp_file_path,
            user_id=user_id,
            task_number=task_number,
            department=department,
            full_name=full_name,
            username=username,
            original_filename=document.file_name or f"document_{document.file_id}"
        )
        
        # Удаляем временный файл
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Получаем количество файлов
        files_count = files_manager.get_user_files_count(
            user_id=user_id,
            task_number=task_number,
            department=department
        )
        
        # Отправляем сообщение о загрузке
        await message.answer(f"✅ Файл сохранен! Всего файлов: {files_count}")
        
        logger.info(f"Файл пользователя {user_id} сохранен: {saved_file_path}")
        
        # Удаляем загрузку из активных и проверяем, была ли это последняя
        is_last_upload = _remove_active_upload(user_id, task_number, upload_id)
        
        # Если это была последняя активная загрузка, обновляем диалог через небольшую задержку
        if is_last_upload:
            await asyncio.sleep(0.3)  # Даем время для завершения других возможных загрузок
            
            # Проверяем еще раз, что нет новых активных загрузок
            if _get_active_uploads_count(user_id, task_number) == 0:
                # Принудительно обновляем данные диалога без смены состояния
                await dialog_manager.update(data={}, show_mode=ShowMode.EDIT)
        
    except Exception as e:
        logger.error(f"Ошибка сохранения файла пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка сохранения файла, попробуйте еще раз")
        
        # Удаляем из активных загрузок в случае ошибки
        _remove_active_upload(user_id, task_number, upload_id)
        
        # Удаляем временный файл в случае ошибки
        temp_file_path = os.path.join("storage/temp", f"temp_{user_id}_{document.file_id}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


async def on_delete_all_files_task_1(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик удаления всех файлов для задания 1"""
    await _handle_delete_all_files(callback, dialog_manager, task_number=1)


async def on_delete_all_files_task_2(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик удаления всех файлов для задания 2"""
    await _handle_delete_all_files(callback, dialog_manager, task_number=2)


async def on_delete_all_files_task_3(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик удаления всех файлов для задания 3"""
    await _handle_delete_all_files(callback, dialog_manager, task_number=3)


async def _handle_delete_all_files(callback: CallbackQuery, dialog_manager: DialogManager, task_number: int):
    """Общий обработчик удаления всех файлов"""
    
    # Сначала отвечаем на callback
    await callback.answer("⏳ Удаляем файлы...")
    
    # Получаем доступ к базе данных
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        await callback.message.answer("❌ Ошибка системы")
        return
    
    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=callback.from_user.id)
        
        if not application:
            await callback.message.answer("❌ Заявка не найдена")
            return
        
        # Определяем отдел для задания
        department = None
        if task_number == 1:
            department = application.department_1
        elif task_number == 2:
            department = application.department_2
        elif task_number == 3:
            department = application.department_3
        
        if not department:
            await callback.message.answer("❌ Отдел не определен")
            return
        
        # Удаляем все файлы
        files_manager = UserFilesManager()
        success = files_manager.delete_all_user_files(
            user_id=callback.from_user.id,
            task_number=task_number,
            department=department
        )
        
        if success:
            # Не отправляем дополнительные сообщения, диалог сам обновится
            pass
        else:
            await callback.message.answer("❌ Ошибка удаления файлов")
        
        logger.info(f"Файлы пользователя {callback.from_user.id} для задания {task_number} удалены")
        
    except Exception as e:
        logger.error(f"Ошибка удаления файлов пользователя {callback.from_user.id}: {e}")
        await callback.message.answer("❌ Ошибка удаления файлов")


async def on_confirm_upload_task_1(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик подтверждения отправки задания 1"""
    await _handle_confirm_upload(callback, dialog_manager, task_number=1)


async def on_confirm_upload_task_2(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик подтверждения отправки задания 2"""
    await _handle_confirm_upload(callback, dialog_manager, task_number=2)


async def on_confirm_upload_task_3(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик подтверждения отправки задания 3"""
    await _handle_confirm_upload(callback, dialog_manager, task_number=3)


async def _handle_confirm_upload(callback: CallbackQuery, dialog_manager: DialogManager, task_number: int):
    """Общий обработчик подтверждения отправки"""
    
    # Сначала отвечаем на callback, чтобы избежать timeout
    await callback.answer("⏳ Обрабатываем...")
    
    # Получаем доступ к базе данных
    db: DB = dialog_manager.middleware_data.get("db")
    
    if not db:
        await callback.message.answer("❌ Ошибка системы")
        return
    
    try:
        # Получаем заявку пользователя
        application: ApplicationsModel = await db.applications.get_application(user_id=callback.from_user.id)
        
        if not application:
            await callback.message.answer("❌ Заявка не найдена")
            return
        
        # Определяем отдел для задания
        department = None
        if task_number == 1:
            department = application.department_1
        elif task_number == 2:
            department = application.department_2
        elif task_number == 3:
            department = application.department_3
        
        if not department:
            await callback.message.answer("❌ Отдел не определен")
            return
        
        # Проверяем, есть ли файлы
        files_manager = UserFilesManager()
        files_count = files_manager.get_user_files_count(
            user_id=callback.from_user.id,
            task_number=task_number,
            department=department
        )
        
        if files_count == 0:
            await callback.message.answer("❌ Сначала загрузите файлы")
            return
        
        # Обновляем статус отправки в БД
        await db.users.set_task_submission_status(user_id=callback.from_user.id, task_number=task_number, submitted=True)
        
        # Определяем состояние для перехода
        if task_number == 1:
            target_state = TasksSG.task_1_submitted
        elif task_number == 2:
            target_state = TasksSG.task_2_submitted
        elif task_number == 3:
            target_state = TasksSG.task_3_submitted
        
        # Переходим к состоянию "отправлено"
        await dialog_manager.switch_to(state=target_state, show_mode=ShowMode.DELETE_AND_SEND)
        
        logger.info(f"Пользователь {callback.from_user.id} подтвердил отправку задания {task_number}")
        
    except Exception as e:
        logger.error(f"Ошибка подтверждения отправки задания {task_number} пользователем {callback.from_user.id}: {e}")
        await callback.message.answer("❌ Ошибка подтверждения отправки")
