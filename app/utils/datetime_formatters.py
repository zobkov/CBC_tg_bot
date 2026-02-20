"""
Утилиты для форматирования дат и времени для онлайн-лекций
"""
from datetime import datetime, timezone, timedelta

# Московское время UTC+3
MOSCOW_TZ = timezone(timedelta(hours=3))

# Русские названия месяцев в родительном падеже
MONTH_NAMES = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def format_moscow_datetime(dt: datetime, include_tz: bool = True) -> str:
    """
    Форматирует datetime в формат "25 октября 2025, 17:00 (МСК)"
    
    Args:
        dt: Datetime объект (с timezone или без)
        include_tz: Включать ли " (МСК)" в конец строки
    
    Returns:
        Отформатированная строка с датой и временем
    """
    # Конвертируем в московское время, если нужно
    if dt.tzinfo is None:
        # Если нет timezone, считаем что это уже Moscow time
        moscow_dt = dt.replace(tzinfo=MOSCOW_TZ)
    else:
        moscow_dt = dt.astimezone(MOSCOW_TZ)
    
    day = moscow_dt.day
    month = MONTH_NAMES[moscow_dt.month]
    year = moscow_dt.year
    time_str = moscow_dt.strftime("%H:%M")
    
    result = f"{day} {month} {year}, {time_str}"
    if include_tz:
        result += " (МСК)"
    
    return result


def format_date_only(dt: datetime) -> str:
    """
    Форматирует только дату в формат "25 октября 2025"
    
    Args:
        dt: Datetime объект
    
    Returns:
        Отформатированная строка с датой
    """
    if dt.tzinfo is None:
        moscow_dt = dt.replace(tzinfo=MOSCOW_TZ)
    else:
        moscow_dt = dt.astimezone(MOSCOW_TZ)
    
    day = moscow_dt.day
    month = MONTH_NAMES[moscow_dt.month]
    year = moscow_dt.year
    
    return f"{day} {month} {year}"


def format_date_short(dt: datetime) -> str:
    """
    Форматирует дату в короткий формат "25.10"
    
    Args:
        dt: Datetime объект
    
    Returns:
        Отформатированная строка с датой в формате DD.MM
    """
    if dt.tzinfo is None:
        moscow_dt = dt.replace(tzinfo=MOSCOW_TZ)
    else:
        moscow_dt = dt.astimezone(MOSCOW_TZ)
    
    return moscow_dt.strftime("%d.%m")


def format_time_only(dt: datetime) -> str:
    """
    Форматирует только время в формат "17:00"
    
    Args:
        dt: Datetime объект
    
    Returns:
        Отформатированная строка со временем
    """
    if dt.tzinfo is None:
        moscow_dt = dt.replace(tzinfo=MOSCOW_TZ)
    else:
        moscow_dt = dt.astimezone(MOSCOW_TZ)
    
    return moscow_dt.strftime("%H:%M")


def is_within_hours(dt: datetime, hours: int) -> bool:
    """
    Проверяет, находится ли дата в пределах N часов от текущего момента
    
    Args:
        dt: Datetime для проверки
        hours: Количество часов
    
    Returns:
        True если dt - hours <= now <= dt, False иначе
    """
    now = datetime.now(timezone.utc)
    
    # Конвертируем в UTC для сравнения
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=MOSCOW_TZ).astimezone(timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)
    
    time_before = dt_utc - timedelta(hours=hours)
    
    return time_before <= now <= dt_utc


def is_link_available(start_at: datetime, hours_before: int = 1) -> bool:
    """
    Проверяет, доступна ли ссылка на лекцию (в пределах N часов до начала)
    
    Args:
        start_at: Время начала лекции
        hours_before: За сколько часов до начала становится доступна ссылка
    
    Returns:
        True если ссылка должна быть доступна
    """
    now = datetime.now(timezone.utc)
    
    # Конвертируем в UTC для сравнения
    if start_at.tzinfo is None:
        start_utc = start_at.replace(tzinfo=MOSCOW_TZ).astimezone(timezone.utc)
    else:
        start_utc = start_at.astimezone(timezone.utc)
    
    time_before = start_utc - timedelta(hours=hours_before)
    
    return now >= time_before


def parse_config_datetime(dt_str: str) -> datetime:
    """
    Парсит datetime из конфига в формате "2025-10-23 10:50:00+03"
    
    Args:
        dt_str: Строка с датой и временем
    
    Returns:
        Datetime объект с timezone
    """
    # Формат: "2025-10-23 10:50:00+03"
    # Заменяем "+03" на "+03:00" для корректного парсинга
    if dt_str.endswith("+03"):
        dt_str = dt_str.replace("+03", "+03:00")
    
    return datetime.fromisoformat(dt_str)


def get_hours_until(dt: datetime) -> float:
    """
    Возвращает количество часов до указанного времени
    Отрицательное значение, если время уже прошло
    
    Args:
        dt: Целевой datetime
    
    Returns:
        Количество часов (может быть отрицательным)
    """
    now = datetime.now(timezone.utc)
    
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=MOSCOW_TZ).astimezone(timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)
    
    delta = dt_utc - now
    return delta.total_seconds() / 3600
