"""
Утилита для проверки дедлайнов и временных ограничений
"""
from datetime import datetime, timezone, timedelta

# Московское время UTC+3
MOSCOW_TZ = timezone(timedelta(hours=3))

# Дедлайн для закрытия тестовых заданий: 3 октября 2025, 06:00 MSK
TASK_SUBMISSION_DEADLINE = datetime(2025, 10, 3, 6, 0, 0, tzinfo=MOSCOW_TZ)

# Дата объявления результатов: 7 октября 2025, 12:00 MSK  
RESULTS_ANNOUNCEMENT_DATE = datetime(2025, 10, 7, 12, 0, 0, tzinfo=MOSCOW_TZ)


def is_task_submission_closed() -> bool:
    """
    Проверяет, закрыта ли отправка тестовых заданий
    Возвращает True, если текущее время >= дедлайна
    """
    now = datetime.now(MOSCOW_TZ)
    return now >= TASK_SUBMISSION_DEADLINE


def get_task_submission_status_message() -> str:
    """
    Возвращает сообщение о закрытии отправки тестовых заданий
    """
    return ("Отправка тестовых заданий закрыта. Результаты буду оглашены 7 октября.\n\n"
            "Тех. поддержка: @zobko")


def format_results_date() -> str:
    """
    Возвращает отформатированную дату объявления результатов
    """
    return RESULTS_ANNOUNCEMENT_DATE.strftime("%d.%m.%Y, %H:%M")