from typing import Any

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from aiogram_dialog import (
    DialogManager
)



# Input error handlers

async def name_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    NotImplemented # TODO

async def phone_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    NotImplemented # TODO

async def email_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    NotImplemented # TODO

# Type factory

async def name_check(value: str) -> str:
    name = value.strip()

    if not name:
        raise ValueError("Имя не может быть пустым")
    if len(name) < 2:
        raise ValueError("Имя должно содержать минимум 2 символа")
    return name

async def email_check(value: str) -> str:
    import re
    email = value.strip().lower()
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Некорректный формат email")
    
    return email

async def phone_check(value: str) -> str:
    import re
    phone = re.sub(r'[^\d+]', '', value)  # Удаляем все кроме цифр и +
    
    # Если номер без +, пытаемся определить код страны
    if not phone.startswith('+'):
        if phone.startswith('8'):
            phone = '+7' + phone[1:]  # Российский формат 8XXXXXXXXXX
        elif phone.startswith('7'):
            phone = '+' + phone       # Российский формат 7XXXXXXXXXX
        elif len(phone) == 10:
            phone = '+7' + phone      # Предполагаем российский номер без кода
        else:
            phone = '+' + phone       # Добавляем + к любому другому номеру
    
    # Проверяем общий формат: + и минимум 10 цифр
    if not re.match(r'^\+\d{10,15}$', phone):
        raise ValueError("Некорректный формат телефона. Используйте международный формат, например: +7XXXXXXXXXX, +1XXXXXXXXXX, +86XXXXXXXXXXX")
    
    return phone