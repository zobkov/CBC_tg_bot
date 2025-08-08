import os
import csv
import logging
from datetime import datetime
from typing import Any

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, Document, User
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput

from config.config import Config
from app.infrastructure.database.database.db import DB
from app.bot.enums.application_status import ApplicationStatus
from app.services.error_monitoring import error_monitor

logger = logging.getLogger(__name__)


async def process_name(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    name = message.text.strip()
    logger.info(f"👤 Пользователь {message.from_user.id} ввел имя: {name}")
    dialog_manager.dialog_data["name"] = name
    await dialog_manager.next()


async def process_surname(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    surname = message.text.strip()
    logger.info(f"👤 Пользователь {message.from_user.id} ввел фамилию: {surname}")
    dialog_manager.dialog_data["surname"] = surname
    await dialog_manager.next()


async def process_patronymic(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    patronymic = message.text.strip()
    logger.info(f"👤 Пользователь {message.from_user.id} ввел отчество: {patronymic}")
    dialog_manager.dialog_data["patronymic"] = patronymic
    # Формируем полное имя
    name = dialog_manager.dialog_data.get("name", "")
    surname = dialog_manager.dialog_data.get("surname", "")
    full_name = f"{surname} {name} {patronymic}".strip()
    dialog_manager.dialog_data["full_name"] = full_name
    logger.info(f"✅ Сформировано полное имя: {full_name}")
    await dialog_manager.next()


async def process_university(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    university = message.text.strip()
    logger.info(f"🏫 Пользователь {message.from_user.id} ввел университет: {university}")
    dialog_manager.dialog_data["university"] = university
    await dialog_manager.next()


async def process_course(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    try:
        course = int(message.text.strip())
        if course < 1 or course > 6:
            logger.warning(f"⚠️ Пользователь {message.from_user.id} ввел некорректный курс: {course}")
            error_monitor.log_validation_error(
                field="course",
                value=str(course),
                user_id=message.from_user.id,
                username=message.from_user.username
            )
            await message.answer("Пожалуйста, введите курс от 1 до 6")
            return
        
        logger.info(f"📚 Пользователь {message.from_user.id} ввел курс: {course}")
        dialog_manager.dialog_data["course"] = str(course)
        await dialog_manager.next()
    except ValueError:
        logger.warning(f"⚠️ Пользователь {message.from_user.id} ввел некорректное значение курса: {message.text}")
        error_monitor.log_validation_error(
            field="course",
            value=message.text,
            user_id=message.from_user.id,
            username=message.from_user.username
        )
        await message.answer("Пожалуйста, введите число от 1 до 6")


async def process_phone(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    phone = message.text.strip()
    logger.info(f"📞 Пользователь {message.from_user.id} ввел телефон: {phone[:4]}***")  # Частично скрываем для безопасности
    
    # Простая валидация телефона
    if len(phone) < 10:
        logger.warning(f"⚠️ Пользователь {message.from_user.id} ввел слишком короткий номер телефона")
        await message.answer("Пожалуйста, введите корректный номер телефона")
        return
        
    dialog_manager.dialog_data["phone"] = phone
    await dialog_manager.next()


async def process_email(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    email = message.text.strip()
    logger.info(f"📧 Пользователь {message.from_user.id} ввел email: {email}")
    
    # Простая валидация email
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        logger.info(f"✅ Email валиден: {email}")
        dialog_manager.dialog_data["email"] = email
        await dialog_manager.next()
    else:
        logger.warning(f"⚠️ Пользователь {message.from_user.id} ввел некорректный email: {email}")
        await message.answer("Пожалуйста, введите корректный email адрес")


async def process_experience(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    experience = message.text.strip()
    logger.info(f"💼 Пользователь {message.from_user.id} ввел опыт работы ({len(experience)} символов)")
    dialog_manager.dialog_data["experience"] = experience
    await dialog_manager.next()


async def process_motivation(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    motivation = message.text.strip()
    logger.info(f"🎯 Пользователь {message.from_user.id} ввел мотивацию ({len(motivation)} символов)")
    dialog_manager.dialog_data["motivation"] = motivation
    await dialog_manager.next()


async def process_resume_file(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    bot: Bot = dialog_manager.middleware_data["bot"]
    document: Document = message.document
    user = message.from_user
    
    logger.info(f"📄 Получен файл от пользователя {user.id} (@{user.username})")
    
    if not document:
        logger.warning(f"⚠️ Пользователь {user.id} не прикрепил файл")
        await message.answer("Пожалуйста, прикрепите файл резюме.")
        return

    # Логируем информацию о файле
    logger.info(f"📋 Информация о файле:")
    logger.info(f"   - Название: {document.file_name}")
    logger.info(f"   - Размер: {document.file_size} байт ({document.file_size / 1024 / 1024:.2f} МБ)")
    logger.info(f"   - MIME-тип: {document.mime_type}")

    # Проверяем размер файла (максимум 20 МБ)
    max_size = 20 * 1024 * 1024
    if document.file_size > max_size:
        logger.warning(f"⚠️ Файл пользователя {user.id} слишком большой: {document.file_size} байт")
        await message.answer("Файл слишком большой. Максимальный размер: 20 МБ")
        return

    # Получаем данные пользователя из диалога
    dialog_data = dialog_manager.dialog_data
    
    # Безопасно получаем имя, фамилию и отчество
    surname = dialog_data.get("surname", "")
    name = dialog_data.get("name", "")
    patronymic = dialog_data.get("patronymic", "")
    
    # Если данные пустые, используем значения по умолчанию
    if not surname or surname.strip() == "":
        surname = "User"
    if not name or name.strip() == "":
        name = "Unknown"
    if not patronymic or patronymic.strip() == "":
        patronymic = "Unknown"

    logger.info(f"👤 Данные пользователя для генерации имени файла:")
    logger.info(f"   - Фамилия: {surname}")
    logger.info(f"   - Имя: {name}")
    logger.info(f"   - Отчество: {patronymic}")

    # Генерируем имя файла
    # Безопасно получаем первые буквы имени и отчества
    name_initial = name[0].upper() if name and len(name) > 0 and name != "Unknown" else "U"
    
    # Для инициалов: если отчества нет, используем только инициал имени
    if patronymic and patronymic.strip() != "" and patronymic != "Unknown":
        patronymic_initial = patronymic[0].upper()
        initials = f"{name_initial}{patronymic_initial}"
        logger.info(f"   📝 Инициалы (с отчеством): {initials}")
    else:
        initials = name_initial
        logger.info(f"   📝 Инициалы (без отчества): {initials}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(document.file_name)[1] if document.file_name else ".pdf"
    new_filename = f"{surname}_{initials}_{user.username or user.id}_{timestamp}{file_extension}"
    
    logger.info(f"📝 Сгенерировано имя файла: {new_filename}")

    try:
        # Получаем файл от Telegram
        file = await bot.get_file(document.file_id)
        file_path = f"app/storage/resumes/{new_filename}"
        
        # Создаем директорию если её нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Скачиваем файл
        await bot.download_file(file.file_path, file_path)
        logger.info(f"✅ Файл резюме скачан локально: {file_path}")
        
        # Проверяем настройки Google Drive
        config: Config = dialog_manager.middleware_data.get("config")
        google_file_url = None
        
        # Google Drive загрузка (опциональная)
        if config and config.google and config.google.enable_drive:
            logger.info(f"🔄 Google Drive включен, начинаем загрузку файла для пользователя {user.id}")
            try:
                from app.services.google_services import GoogleServicesManager
                import asyncio
                
                # Создаем менеджер Google сервисов с параметрами из конфига
                google_manager = GoogleServicesManager(
                    credentials_path=config.google.credentials_path,
                    spreadsheet_id=config.google.spreadsheet_id,
                    drive_folder_id=config.google.drive_folder_id or "",
                    enable_drive=config.google.enable_drive
                )
                
                logger.info(f"🚀 Запускаем загрузку файла {new_filename} в Google Drive...")
                
                # Запускаем загрузку в отдельном потоке (так как метод синхронный)
                loop = asyncio.get_event_loop()
                google_file_url = await loop.run_in_executor(
                    None, 
                    google_manager.upload_file_to_drive,
                    file_path,
                    new_filename
                )
                
                if google_file_url:
                    logger.info(f"✅ Файл успешно загружен в Google Drive: {google_file_url}")
                    dialog_manager.dialog_data["resume_google_url"] = google_file_url
                else:
                    logger.error("❌ Не удалось загрузить файл в Google Drive - получен пустой URL")
                    dialog_manager.dialog_data["resume_google_error"] = "Не удалось получить URL файла в Google Drive"
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Ошибка загрузки резюме в Google Drive: {e}")
                
                # Определяем тип ошибки для более понятного сообщения пользователю
                if "Service Accounts do not have storage quota" in error_msg:
                    user_error_msg = "Необходимо настроить общий диск Google"
                    logger.warning("⚠️ Google Drive: сервисный аккаунт не имеет квоты хранилища - нужен Shared Drive")
                elif "storageQuotaExceeded" in error_msg:
                    user_error_msg = "На Google Drive недостаточно места"
                    logger.warning("⚠️ Google Drive: превышена квота хранилища")
                elif "quotaExceeded" in error_msg:
                    user_error_msg = "Превышены лимиты Google Drive API"
                    logger.warning("⚠️ Google Drive: превышены лимиты API")
                elif "403" in error_msg:
                    user_error_msg = "Нет доступа к Google Drive"
                    logger.warning("⚠️ Google Drive: ошибка доступа (403)")
                elif "401" in error_msg:
                    user_error_msg = "Ошибка авторизации Google Drive"
                    logger.warning("⚠️ Google Drive: ошибка авторизации (401)")
                elif "404" in error_msg:
                    user_error_msg = "Папка на Google Drive не найдена"
                    logger.warning("⚠️ Google Drive: папка не найдена (404)")
                else:
                    user_error_msg = f"Техническая ошибка Google Drive"
                    logger.error(f"⚠️ Google Drive: неизвестная ошибка - {error_msg}")
                
                dialog_manager.dialog_data["resume_google_error"] = user_error_msg
        else:
            if not config:
                logger.warning("⚠️ Конфигурация не найдена - Google Drive отключен")
            elif not config.google:
                logger.info("ℹ️ Google Services не настроены")
            elif not config.google.enable_drive:
                logger.info("ℹ️ Google Drive отключен в конфигурации")
        
        # Сохраняем информацию о файле в данных диалога
        dialog_manager.dialog_data["resume_file"] = new_filename
        
        # Подготавливаем сообщение пользователю
        message_text = f"✅ Резюме получено и сохранено как: {new_filename}\n"
        
        if google_file_url:
            message_text += "📁 Файл также загружен в Google Drive\n"
        elif config and config.google and config.google.enable_drive:
            error = dialog_manager.dialog_data.get("resume_google_error", "")
            message_text += f"⚠️ Файл сохранен локально, но не загружен в Google Drive: {error}\n"
        else:
            message_text += "📋 Файл сохранен локально (Google Drive отключен)\n"
            
        message_text += "Теперь вы можете перейти к следующему шагу."
        
        await message.answer(message_text)
        
        # ВАЖНО: Переходим к следующему окну диалога
        logger.info(f"➡️ Переходим к следующему окну диалога для пользователя {user.id}")
        await dialog_manager.next()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке файла резюме: {e}")
        await message.answer("Произошла ошибка при обработке файла. Попробуйте еще раз.")
        return


async def on_confirm_application(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик подтверждения заявки"""
    await save_application(dialog_manager)
    await dialog_manager.next()


async def save_application(dialog_manager: DialogManager):
    """Сохранение заявки в БД и экспорт"""
    from aiogram.types import User
    
    event_from_user: User = dialog_manager.event.from_user
    dialog_data = dialog_manager.dialog_data
    config: Config = dialog_manager.middleware_data.get("config")
    db: DB = dialog_manager.middleware_data.get("db")
    
    logger.info(f"🎯 Начинаем сохранение заявки пользователя {event_from_user.id} (@{event_from_user.username})")
    
    if not config or not db:
        logger.error("❌ Критическая ошибка: нет доступа к конфигурации или БД")
        if not config:
            logger.error("❌ Config объект отсутствует")
        if not db:
            logger.error("❌ DB объект отсутствует")
        return
    
    logger.info(f"✅ Конфигурация и БД доступны")
    
    # Получаем данные резюме (уже обработанные в process_resume_file)
    resume_local_path = None
    resume_google_drive_url = None
    
    resume_filename = dialog_data.get("resume_file")
    if resume_filename:
        resume_local_path = f"app/storage/resumes/{resume_filename}"
        resume_google_drive_url = dialog_data.get("resume_google_url", "")
        logger.info(f"📄 Файл резюме: {resume_filename}")
        if resume_google_drive_url:
            logger.info(f"☁️ Google Drive URL: {resume_google_drive_url}")
        else:
            logger.info(f"💾 Только локальное сохранение резюме")
    else:
        logger.warning("⚠️ Файл резюме не загружен")
    
    logger.info(f"📊 Подготавливаем данные заявки...")
    
    # Парсим текстовые данные с защитой от ошибок
    try:
        how_found_idx = int(dialog_data.get("how_found_kbk", "0"))
        how_found_text = config.selection.how_found_options[how_found_idx] if how_found_idx < len(config.selection.how_found_options) else ""
        logger.info(f"🔍 Как узнал о КБК: {how_found_text}")
    except (ValueError, IndexError) as e:
        logger.error(f"❌ Ошибка обработки 'how_found_kbk': {e}")
        how_found_text = ""
    
    try:
        department_key = dialog_data.get("selected_department", "")
        department_name = config.selection.departments.get(department_key, {}).get("name", "")
        logger.info(f"🏢 Выбранный департамент: {department_name} ({department_key})")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки департамента: {e}")
        department_name = ""
    
    try:
        position_idx = int(dialog_data.get("selected_position", "0"))
        if department_key in config.selection.departments:
            positions = config.selection.departments[department_key]["positions"]
            position_text = positions[position_idx] if position_idx < len(positions) else ""
        else:
            position_text = ""
        logger.info(f"💼 Выбранная позиция: {position_text}")
    except (ValueError, IndexError, KeyError) as e:
        logger.error(f"❌ Ошибка обработки позиции: {e}")
        position_text = ""
    
    # Логируем все собранные данные
    logger.info(f"👤 ФИО: {dialog_data.get('full_name', 'не указано')}")
    logger.info(f"🎓 Университет: {dialog_data.get('university', 'не указано')}")
    logger.info(f"📚 Курс: {dialog_data.get('course', 'не указано')}")
    logger.info(f"📞 Телефон: {dialog_data.get('phone', 'не указано')}")
    logger.info(f"📧 Email: {dialog_data.get('email', 'не указано')}")
    
    # Сохраняем в БД и меняем статус на submitted
    logger.info(f"💾 Сохраняем заявку в базу данных...")
    try:
        await db.applications.update_first_stage_form(
            user_id=event_from_user.id,
            full_name=dialog_data.get("full_name", ""),
            university=dialog_data.get("university", ""),
            course=int(dialog_data.get("course", "1")),
            phone=dialog_data.get("phone", ""),
            email=dialog_data.get("email", ""),
            telegram_username=event_from_user.username or "",
            how_found_kbk=how_found_text,
            department=department_name,
            position=position_text,
            experience=dialog_data.get("experience", ""),
            motivation=dialog_data.get("motivation", ""),
            resume_local_path=resume_local_path,
            resume_google_drive_url=resume_google_drive_url
        )
        
        logger.info(f"✅ Данные заявки сохранены в БД")
        
        # Обновляем статус на SUBMITTED
        logger.info(f"🔄 Обновляем статус заявки на SUBMITTED...")
        await db.applications.update_application_status(
            user_id=event_from_user.id,
            status=ApplicationStatus.SUBMITTED
        )
        
        logger.info(f"✅ Статус заявки обновлен на SUBMITTED")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при сохранении в БД: {e}")
        logger.error(f"📋 Данные заявки: {dialog_data}")
        return
    
    # Подготавливаем данные для экспорта
    logger.info(f"📤 Подготавливаем данные для экспорта...")
    
    application_data = {
        'timestamp': datetime.now().isoformat(),
        'user_id': event_from_user.id,
        'username': event_from_user.username or "",
        'full_name': dialog_data.get("full_name", ""),
        'university': dialog_data.get("university", ""),
        'course': dialog_data.get("course", "1"),
        'phone': dialog_data.get("phone", ""),
        'email': dialog_data.get("email", ""),
        'how_found_kbk': how_found_text,
        'department': department_name,
        'position': position_text,
        'experience': dialog_data.get("experience", ""),
        'motivation': dialog_data.get("motivation", ""),
        'status': 'submitted',
        'resume_local_path': resume_local_path or "",
        'resume_google_drive_url': resume_google_drive_url or ""
    }
    
    logger.info(f"📊 Данные для экспорта подготовлены")
    
    # Сохраняем в CSV для бекапа
    logger.info(f"💾 Сохраняем резервную копию в CSV...")
    try:
        await save_to_csv(application_data)
        logger.info(f"✅ Резервная копия сохранена в CSV")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в CSV: {e}")
    
    # Отправляем в Google Sheets если настроено
    if config.google:
        logger.info(f"☁️ Отправляем данные в Google Sheets...")
        try:
            from app.services.google_services import GoogleServicesManager
            google_manager = GoogleServicesManager(
                credentials_path=config.google.credentials_path,
                spreadsheet_id=config.google.spreadsheet_id,
                drive_folder_id=config.google.drive_folder_id,
                enable_drive=config.google.enable_drive
            )
            logger.info(f"📊 GoogleServicesManager инициализирован (Drive: {'включен' if config.google.enable_drive else 'отключен'})")
            
            success = await google_manager.add_application_to_sheet(application_data)
            if success:
                logger.info("✅ Заявка успешно добавлена в Google Sheets")
            else:
                logger.error("❌ Не удалось добавить заявку в Google Sheets")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке в Google Sheets: {e}")
            if "quotaExceeded" in str(e):
                logger.error("💡 Возможно превышены лимиты Google Sheets API")
            elif "403" in str(e):
                logger.error("💡 Проверьте права доступа к Google Sheets")
            elif "404" in str(e):
                logger.error("💡 Проверьте ID таблицы Google Sheets")
    else:
        logger.info("ℹ️ Google Sheets не настроен, пропускаем экспорт")
    
    logger.info(f"🎉 Сохранение заявки пользователя {event_from_user.id} завершено успешно!")


async def save_to_csv(application_data: dict):
    """Сохранение данных в CSV файл"""
    import csv
    logger.info(f"📝 Сохраняем данные в CSV файл...")
    
    try:
        # Создаем директорию если её нет
        backup_dir = "app/storage/backups"
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"📁 Директория {backup_dir} подготовлена")
        
        csv_path = f"{backup_dir}/applications.csv"
        file_exists = os.path.exists(csv_path)
        
        logger.info(f"📄 Путь к CSV файлу: {csv_path}")
        logger.info(f"📄 Файл существует: {file_exists}")
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'timestamp', 'user_id', 'username', 'full_name', 'university', 
                'course', 'phone', 'email', 'how_found_kbk', 'department', 
                'position', 'experience', 'motivation', 'status', 
                'resume_local_path', 'resume_google_drive_url'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                logger.info("📋 Создаем заголовки CSV файла...")
                writer.writeheader()
            
            logger.info("📝 Записываем данные заявки в CSV...")
            writer.writerow(application_data)
            logger.info("✅ Данные успешно записаны в CSV")
            
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в CSV: {e}")
        raise


# Дополнительные обработчики для совместимости с dialogs.py
async def on_apply_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Начало заполнения заявки"""
    logger.info(f"🚀 Пользователь {callback.from_user.id} начал заполнение заявки")
    await dialog_manager.next()

async def on_full_name_input(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка ввода полного имени"""
    full_name = message.text.strip()
    logger.info(f"👤 Получено ФИО: {full_name} от пользователя {message.from_user.id}")
    
    # Разбиваем ФИО на части (Фамилия Имя Отчество)
    name_parts = full_name.split()
    
    if len(name_parts) >= 1:
        surname = name_parts[0]  # Первая часть - фамилия
        dialog_manager.dialog_data["surname"] = surname
        logger.info(f"   📝 Фамилия: {surname}")
    else:
        dialog_manager.dialog_data["surname"] = "User"
        logger.warning(f"⚠️ Не удалось извлечь фамилию из: {full_name}")
    
    if len(name_parts) >= 2:
        name = name_parts[1]  # Вторая часть - имя
        dialog_manager.dialog_data["name"] = name
        logger.info(f"   📝 Имя: {name}")
    else:
        dialog_manager.dialog_data["name"] = "Unknown"
        logger.warning(f"⚠️ Не удалось извлечь имя из: {full_name}")
    
    if len(name_parts) >= 3:
        patronymic = name_parts[2]  # Третья часть - отчество
        dialog_manager.dialog_data["patronymic"] = patronymic
        logger.info(f"   📝 Отчество: {patronymic}")
    else:
        dialog_manager.dialog_data["patronymic"] = ""  # Отчество может отсутствовать
        logger.info(f"   📝 Отчество: не указано")
    
    # Сохраняем полное имя
    dialog_manager.dialog_data["full_name"] = full_name
    
    logger.info(f"✅ ФИО успешно разобрано для пользователя {message.from_user.id}")
    await dialog_manager.next()

async def on_university_input(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка ввода университета"""
    university = message.text.strip()
    logger.info(f"🏫 Получен университет: {university} от пользователя {message.from_user.id}")
    dialog_manager.dialog_data["university"] = university
    await dialog_manager.next()

async def on_phone_input(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка ввода телефона"""
    phone = message.text.strip()
    logger.info(f"📞 Получен телефон: {phone} от пользователя {message.from_user.id}")
    
    # Простая валидация телефона
    if len(phone) >= 10:
        dialog_manager.dialog_data["phone"] = phone
        await dialog_manager.next()
    else:
        logger.warning(f"⚠️ Некорректный телефон от пользователя {message.from_user.id}: {phone}")
        await message.answer("Пожалуйста, введите корректный номер телефона (минимум 10 цифр)")

async def on_email_input(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка ввода email"""
    email = message.text.strip()
    logger.info(f"📧 Получен email: {email} от пользователя {message.from_user.id}")
    
    if "@" in email and "." in email:
        dialog_manager.dialog_data["email"] = email
        await dialog_manager.next()
    else:
        logger.warning(f"⚠️ Некорректный email от пользователя {message.from_user.id}: {email}")
        await message.answer("Пожалуйста, введите корректный email адрес")

async def on_course_selected(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id, **kwargs):
    """Обработка выбора курса"""
    logger.info(f"📚 Выбран курс: {item_id} пользователем {callback.from_user.id}")
    dialog_manager.dialog_data["course"] = item_id
    await dialog_manager.next()

async def on_how_found_selected(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id, **kwargs):
    """Обработка выбора способа узнавания о КБК"""
    logger.info(f"🔍 Выбран способ узнавания: {item_id} пользователем {callback.from_user.id}")
    dialog_manager.dialog_data["how_found_kbk"] = item_id
    await dialog_manager.next()

async def on_department_selected(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id, **kwargs):
    """Обработка выбора департамента"""
    logger.info(f"🏢 Выбран департамент: {item_id} пользователем {callback.from_user.id}")
    dialog_manager.dialog_data["selected_department"] = item_id
    await dialog_manager.next()

async def on_position_selected(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id, **kwargs):
    """Обработка выбора позиции"""
    logger.info(f"💼 Выбрана позиция: {item_id} пользователем {callback.from_user.id}")
    dialog_manager.dialog_data["selected_position"] = item_id
    await dialog_manager.next()

async def on_experience_input(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка ввода опыта"""
    experience = message.text.strip()
    logger.info(f"💼 Получен опыт от пользователя {message.from_user.id}: {len(experience)} символов")
    dialog_manager.dialog_data["experience"] = experience
    await dialog_manager.next()

async def on_motivation_input(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка ввода мотивации"""
    motivation = message.text.strip()
    logger.info(f"💭 Получена мотивация от пользователя {message.from_user.id}: {len(motivation)} символов")
    dialog_manager.dialog_data["motivation"] = motivation
    await dialog_manager.next()

async def on_resume_uploaded(message: Message, widget, dialog_manager: DialogManager, **kwargs):
    """Обработка загрузки резюме"""
    logger.info(f"📎 Начинаем обработку резюме от пользователя {message.from_user.id}")
    await process_resume_file(message, widget, dialog_manager, **kwargs)
