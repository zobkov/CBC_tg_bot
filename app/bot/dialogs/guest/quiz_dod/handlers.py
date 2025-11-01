import logging
from typing import Any

from aiogram.types import CallbackQuery, Message

from better_profanity import profanity

from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select

from .questions import QUESTIONS
from .states import QuizDodSG

logger = logging.getLogger(__name__)


# Input error handlers

async def name_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    message.answer(f"{error_}")

async def phone_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    message.answer(f"{error_}")

async def email_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    message.answer(f"{error_}")

# Type factory

def name_check(value: str) -> str:
    profanity.load_censor_words()
    name = value.strip()

    logger.debug(f"Profanity is in name: {profanity.censor(name)}")

    if not name:
        raise ValueError("Имя не может быть пустым")
    if len(name) < 2:
        raise ValueError("Имя должно содержать минимум 2 символа")
    if profanity.contains_profanity(name):
        raise ValueError("Имя не может содержать нецензурных выражений!")
    return name

def email_check(value: str) -> str:
    import re
    email = value.strip().lower()
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Некорректный формат email")
    
    return email

def phone_check(value: str) -> str:
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


def _reset_quiz_progress(manager: DialogManager) -> None:
    """Сбрасывает прогресс квиза перед новым прохождением."""
    manager.dialog_data["quiz_dod_question_index"] = 0
    manager.dialog_data["quiz_dod_correct_answers"] = 0
    manager.dialog_data["quiz_dod_best_updated"] = False


async def mock_save_quiz_result(user_id: int, score: int) -> None:
    """Мок сохранения результата квиза в базу данных."""
    logger.info("[QUIZ_DOD][MOCK] Save result user=%s score=%s", user_id, score)


async def on_quiz_start(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    **kwargs,
):
    await callback.answer()
    _reset_quiz_progress(dialog_manager)
    dialog_manager.dialog_data["quiz_dod_last_score"] = 0
    await dialog_manager.switch_to(QuizDodSG.name)


async def on_name_entered(
    message: Message,
    widget,
    dialog_manager: DialogManager,
    value: str,
    **kwargs,
):
    dialog_manager.dialog_data["quiz_dod_name"] = value
    await dialog_manager.next()


async def on_phone_entered(
    message: Message,
    widget,
    dialog_manager: DialogManager,
    value: str,
    **kwargs,
):
    dialog_manager.dialog_data["quiz_dod_phone"] = value
    await dialog_manager.next()


async def on_email_entered(
    message: Message,
    widget,
    dialog_manager: DialogManager,
    value: str,
    **kwargs,
):
    dialog_manager.dialog_data["quiz_dod_email"] = value
    dialog_manager.dialog_data["quiz_dod_last_score"] = 0
    _reset_quiz_progress(dialog_manager)
    await dialog_manager.switch_to(
        QuizDodSG.QUESTIONS,
        show_mode=ShowMode.DELETE_AND_SEND,
    )


async def on_quiz_answer_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    **kwargs,
):
    await callback.answer()

    dialog_data = dialog_manager.dialog_data
    question_index = dialog_data.get("quiz_dod_question_index", 0)
    selected_option = int(item_id)

    if question_index < len(QUESTIONS):
        question = QUESTIONS[question_index]
        if selected_option == question.correct:
            dialog_data["quiz_dod_correct_answers"] = dialog_data.get("quiz_dod_correct_answers", 0) + 1

    dialog_data["quiz_dod_question_index"] = question_index + 1

    if dialog_data["quiz_dod_question_index"] >= len(QUESTIONS):
        score = dialog_data.get("quiz_dod_correct_answers", 0)
        dialog_data["quiz_dod_last_score"] = score

        previous_best = dialog_data.get("quiz_dod_score")
        if previous_best is None or score > previous_best:
            dialog_data["quiz_dod_score"] = score
            dialog_data["quiz_dod_best_updated"] = True
        else:
            dialog_data["quiz_dod_best_updated"] = False

        await mock_save_quiz_result(callback.from_user.id, score)

        await callback.message.answer("""Мы очень ценим твою активность ❤️ 

В знак благодарности приготовили для тебя небольшой подарок – цифровой стикерпак с нашим маскотом 

Ниже – один из стикеров. Сохраняй скорей и используй его в чатах и комментариях – пусть все знают, что ты на стороне КБК 💪🏻""")

        await callback.message.answer_sticker('CAACAgIAAxkBAAETmC9pBlc9BAjTquUvcGJ0a04ZH4g6dAACwGoAAkEIMElCkBSwcWM0rDYE')

        await dialog_manager.switch_to(
            QuizDodSG.RESULTS,
            show_mode=ShowMode.DELETE_AND_SEND,
        )
        return

    await dialog_manager.switch_to(
        QuizDodSG.QUESTIONS,
        show_mode=ShowMode.DELETE_AND_SEND,
    )


async def on_quiz_restart(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    **kwargs,
):
    await callback.answer()
    _reset_quiz_progress(dialog_manager)
    dialog_manager.dialog_data["quiz_dod_last_score"] = 0
    await dialog_manager.switch_to(
        QuizDodSG.QUESTIONS,
        show_mode=ShowMode.DELETE_AND_SEND,
    )