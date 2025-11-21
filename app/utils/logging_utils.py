"""Утилиты для расширенного логирования и настройки уровней."""
import functools
import logging
from datetime import datetime
from typing import Any, Callable, Dict

# Custom log levels placed between DEBUG (10) and INFO (20) to keep verbose flow
SQLALCHEMY_DEBUG_LEVEL = logging.DEBUG + 1
AIOGRAM_DEBUG_LEVEL = logging.DEBUG + 2
AIOGRAM_DIALOG_DEBUG_LEVEL = logging.DEBUG + 3


def _make_logger_method(level: int):
    """Generate a bound logger method for emitting records at a custom level."""

    def log_for_level(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(level):
            logging.Logger.log(self, level, message, *args, **kwargs)

    return log_for_level


def register_custom_log_levels() -> None:
    """Register custom log levels and helper methods once per interpreter."""
    custom_levels: Dict[int, tuple[str, str]] = {
        SQLALCHEMY_DEBUG_LEVEL: ("SQLALCHEMY#DEBUG", "sqlalchemy_debug"),
        AIOGRAM_DEBUG_LEVEL: ("AIOGRAM#DEBUG", "aiogram_debug"),
        AIOGRAM_DIALOG_DEBUG_LEVEL: ("AIOGRAM_DIALOG#DEBUG", "aiogram_dialog_debug"),
    }

    for level, (name, method_name) in custom_levels.items():
        if logging.getLevelName(level) != name:
            logging.addLevelName(level, name)

        if not hasattr(logging.Logger, method_name):
            setattr(logging.Logger, method_name, _make_logger_method(level))


register_custom_log_levels()


class LoggerLevelOverrideFilter(logging.Filter):
    """Remap DEBUG records from selected loggers to dedicated custom levels."""

    def __init__(self, overrides: Dict[str, int]):
        super().__init__()
        self._overrides = overrides

    def filter(self, record: logging.LogRecord) -> bool:
        for logger_name, level in self._overrides.items():
            if record.name == logger_name or record.name.startswith(f"{logger_name}."):
                if record.levelno == logging.DEBUG and record.levelno != level:
                    record.levelno = level
                    record.levelname = logging.getLevelName(level)
                break
        return True


class HandlerLevelToggleFilter(logging.Filter):
    """Filter records by allowing only explicitly enabled level names."""

    def __init__(self, levels: Dict[str, bool]):
        super().__init__()
        # Uppercase names for case-insensitive matching and keep only truthy ones
        self._approved_levels = {
            name.upper(): bool(is_enabled) for name, is_enabled in levels.items() if bool(is_enabled)
        }

    def filter(self, record: logging.LogRecord) -> bool:
        if not self._approved_levels:
            return True
        return record.levelname.upper() in self._approved_levels


logger = logging.getLogger(__name__)


def log_user_action(action_name: str, log_level: int = logging.INFO):
    """
    Декоратор для логирования действий пользователя
    
    Args:
        action_name: Название действия для логирования
        log_level: Уровень логирования
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Извлекаем информацию о пользователе из аргументов
            user_id = None
            username = None
            
            for arg in args:
                if hasattr(arg, 'from_user'):
                    user_id = arg.from_user.id
                    username = arg.from_user.username
                    break
                if hasattr(arg, 'event') and hasattr(arg.event, 'from_user'):
                    user_id = arg.event.from_user.id
                    username = arg.event.from_user.username
                    break
            
            start_time = datetime.now()
            
            # Логируем начало действия
            logger.log(
                log_level,
                "🎯 %s | Пользователь: %s (@%s) | Начало",
                action_name,
                user_id,
                username,
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # Логируем успешное завершение
                duration = (datetime.now() - start_time).total_seconds()
                logger.log(
                    log_level,
                    "✅ %s | Пользователь: %s | Завершено за %.2fс",
                    action_name,
                    user_id,
                    duration,
                )
                
                return result
                
            except Exception as e:
                # Логируем ошибку
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    "❌ %s | Пользователь: %s | Ошибка за %.2fс: %s",
                    action_name,
                    user_id,
                    duration,
                    e,
                )
                raise
                
        return wrapper
    return decorator


def log_data_operation(operation_name: str, sensitive_fields: list = None):
    """
    Декоратор для логирования операций с данными
    
    Args:
        operation_name: Название операции
        sensitive_fields: Список полей, которые нужно скрыть в логах
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'credentials']
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            # Маскируем чувствительные данные
            safe_kwargs = {}
            for key, value in kwargs.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    safe_kwargs[key] = "***MASKED***"
                else:
                    safe_kwargs[key] = str(value)[:100]  # Ограничиваем длину для читаемости
            
            logger.info("📊 %s | Начало | Параметры: %s", operation_name, safe_kwargs)
            
            try:
                result = await func(*args, **kwargs)
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.info("✅ %s | Успешно завершено за %.2fс", operation_name, duration)
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error("❌ %s | Ошибка за %.2fс: %s", operation_name, duration, e)
                raise
                
        return wrapper
    return decorator


def log_api_call(service_name: str, endpoint: str = None):
    """
    Декоратор для логирования API вызовов
    
    Args:
        service_name: Название сервиса (Google Drive, Google Sheets, etc.)
        endpoint: Конечная точка API
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            endpoint_info = f" | Endpoint: {endpoint}" if endpoint else ""
            logger.info("🌐 API Call | %s%s | Начало", service_name, endpoint_info)
            
            try:
                result = await func(*args, **kwargs)
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.info("✅ API Call | %s | Успешно за %.2fс", service_name, duration)
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                error_type = type(e).__name__
                
                # Специальная обработка API ошибок
                if "403" in str(e):
                    logger.warning("🚫 API Call | %s | Доступ запрещен (403) за %.2fс", service_name, duration)
                elif "401" in str(e):
                    logger.warning("🔐 API Call | %s | Неавторизован (401) за %.2fс", service_name, duration)
                elif "404" in str(e):
                    logger.warning("🔍 API Call | %s | Не найдено (404) за %.2fс", service_name, duration)
                elif "quotaExceeded" in str(e) or "storageQuotaExceeded" in str(e):
                    logger.warning("📊 API Call | %s | Превышена квота за %.2fс", service_name, duration)
                else:
                    logger.error("❌ API Call | %s | %s за %.2fс: %s", service_name, error_type, duration, e)
                
                raise
                
        return wrapper
    return decorator


class ProcessLogger:
    """Класс для подробного логирования процессов"""
    
    def __init__(self, process_name: str, user_id: int = None):
        self.process_name = process_name
        self.user_id = user_id
        self.start_time = datetime.now()
        self.steps = []
        
    def step(self, step_name: str, details: str = None):
        """Логирует шаг процесса"""
        timestamp = datetime.now()
        duration = (timestamp - self.start_time).total_seconds()
        
        step_info = f"📋 {self.process_name} | Шаг: {step_name}"
        if self.user_id:
            step_info += f" | Пользователь: {self.user_id}"
        step_info += f" | +{duration:.2f}с"
        
        if details:
            step_info += f" | {details}"
            
        logger.info("%s", step_info)
        
        self.steps.append({
            'step': step_name,
            'timestamp': timestamp.isoformat(),
            'duration': duration,
            'details': details
        })
    
    def complete(self, success: bool = True, final_message: str = None):
        """Завершает процесс"""
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        status = "✅ Успешно" if success else "❌ С ошибкой"
        completion_info = f"🏁 {self.process_name} | {status} | Общее время: {total_duration:.2f}с"
        
        if self.user_id:
            completion_info += f" | Пользователь: {self.user_id}"
            
        if final_message:
            completion_info += f" | {final_message}"
            
        logger.info("%s", completion_info)
        
        # Логируем сводку по шагам
        if self.steps:
            logger.debug("📊 %s | Сводка по шагам: %d шагов", self.process_name, len(self.steps))
            for i, step in enumerate(self.steps, 1):
                logger.debug("   %d. %s (%.2fс)", i, step['step'], step['duration'])


def create_process_logger(process_name: str, user_id: int = None) -> ProcessLogger:
    """Создает новый логгер процесса"""
    return ProcessLogger(process_name, user_id)


# Готовые декораторы для частых операций
database_operation = log_data_operation
google_api_call = log_api_call
user_action = log_user_action

# Примеры использования:
# @user_action("Загрузка резюме")
# async def upload_resume(...)

# @google_api_call("Google Drive", "files.create")  
# async def upload_to_drive(...)

# @database_operation("Сохранение заявки")
# async def save_application(...)
