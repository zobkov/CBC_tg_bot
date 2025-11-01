import asyncio
import logging
from typing import Any

from aiogram.types import CallbackQuery, Message, FSInputFile

from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select

from app.infrastructure.database.database.db import DB
from app.utils.certificate_gen import (
    CertificateGenerationError,
    get_certificate_generator,
)
from better_profanity import profanity
from .questions import QUESTIONS
from .states import QuizDodSG
from .profanity_list import RUSSIAN_PROFANITY

logger = logging.getLogger(__name__)

_PROFANITY_LOADED = False
_CERTIFICATE_GENERATOR = get_certificate_generator()


def _ensure_profanity_loaded() -> None:
    """Загружает кастомный список нецензурных слов один раз."""
    global _PROFANITY_LOADED
    if _PROFANITY_LOADED:
        return

    profanity.load_censor_words()
    profanity.add_censor_words(RUSSIAN_PROFANITY)
    _PROFANITY_LOADED = True


# Input error handlers

async def name_error_handler(
        message: Message,
        dialog_: Any,
        manager: DialogManager,
        error_: ValueError
):
    logger.debug(f"Wrong name. Error: {error_}")

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

async def education_error_handler(
    message: Message,
    dialog_: Any,
    manager: DialogManager,
    error_: ValueError
):
    message.answer(f"{error_}")

# Type factory

def name_check(value: str) -> str:
    _ensure_profanity_loaded()
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


def education_check(value: str) -> str:
    education = value.strip()

    if not education:
        raise ValueError("Поле не может быть пустым. Пожалуйста, укажи учебное заведение и курс или класс.")

    if len(education) < 3:
        raise ValueError("Укажи, пожалуйста, полное название учебного заведения и класс/курс.")

    return education


def _reset_quiz_progress(manager: DialogManager) -> None:
    """Сбрасывает прогресс квиза перед новым прохождением."""
    manager.dialog_data["quiz_dod_question_index"] = 0
    manager.dialog_data["quiz_dod_correct_answers"] = 0
    manager.dialog_data["quiz_dod_best_updated"] = False


async def _send_quiz_certificate(message: Message, dialog_manager: DialogManager) -> bool:
    """Генерирует персональный сертификат и отправляет его пользователю."""
    full_name = dialog_manager.dialog_data.get("quiz_dod_name")
    if not full_name:
        logger.warning("[QUIZ_DOD] Skip certificate generation: name missing in dialog data")
        await message.answer(
            "Не получилось найти твои данные для сертификата. Попробуй пройти квиз ещё раз, пожалуйста."
        )
        return False

    loop = asyncio.get_running_loop()
    try:
        certificate_path = await loop.run_in_executor(
            None,
            _CERTIFICATE_GENERATOR.generate,
            full_name,
        )
    except CertificateGenerationError as exc:
        logger.exception("[QUIZ_DOD] Failed to generate certificate for name=%s", full_name)
        await message.answer(
            "Не удалось подготовить сертификат. Попробуем ещё раз после следующего прохождения квиза 🙈",
        )
        await message.answer(
            "Служебная информация для команды поддержки:\n" f"{exc}",
        )
        return False

    success = False
    try:
        await message.answer_document(
            document=FSInputFile(certificate_path),
            caption="Твой персональный сертификат участника квиза! 🎉",
        )
        success = True
    except Exception:  # noqa: BLE001 - важно залогировать полную ошибку
        logger.exception("[QUIZ_DOD] Failed to send certificate %s", certificate_path)
        await message.answer(
            "Мы не смогли отправить файл сертификата. Попробуй, пожалуйста, чуть позже.",
        )
    finally:
        try:
            certificate_path.unlink(missing_ok=True)
        except OSError:
            logger.warning(
                "[QUIZ_DOD] Unable to remove temporary certificate file %s",
                certificate_path,
            )

    return success


async def save_quiz_result(dialog_manager: DialogManager, user_id: int, score: int) -> None:
    """Сохраняет лучший результат квиза в базе данных."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    if not db:
        logger.warning("[QUIZ_DOD] Database unavailable; skip saving for user=%s", user_id)
        return

    try:
        await db.quiz_dod.upsert_best_result(user_id=user_id, quiz_result=score)
        logger.info("[QUIZ_DOD] Save result user=%s score=%s", user_id, score)
    except Exception:
        logger.exception("[QUIZ_DOD] Failed to save quiz result user=%s score=%s", user_id, score)


async def save_user_info(
    dialog_manager: DialogManager,
    user_id: int,
    *,
    full_name: str,
    phone: str,
    email: str,
    education: str,
) -> None:
    """Сохраняет информацию пользователя из мини-анкеты."""
    db: DB | None = dialog_manager.middleware_data.get("db")
    if not db:
        logger.warning("[QUIZ_DOD] Database unavailable; skip saving user info for user=%s", user_id)
        return

    try:
        await db.quiz_dod_users_info.upsert_user_info(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            email=email,
            education=education,
        )
        logger.info("[QUIZ_DOD] Saved user info user=%s", user_id)
    except Exception:
        logger.exception("[QUIZ_DOD] Failed to save user info user=%s", user_id)


async def on_certificate_requested(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    **kwargs,
):
    await callback.answer()

    if dialog_manager.dialog_data.get("quiz_dod_certificate_sent"):
        await callback.message.answer("Мы уже отправили тебе сертификат. Проверь чат 📄")
        return

    certificate_sent = await _send_quiz_certificate(callback.message, dialog_manager)
    if not certificate_sent:
        return

    dialog_manager.dialog_data["quiz_dod_certificate_sent"] = True

    db: DB | None = dialog_manager.middleware_data.get("db")
    user = callback.from_user

    if db and user:
        try:
            await db.quiz_dod_users_info.mark_certificate_requested(user.id)
        except Exception:
            logger.exception("[QUIZ_DOD] Failed to mark certificate requested for user=%s", user.id)

    await callback.message.answer("Готово! Сертификат уже у тебя 🎉")


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
    await dialog_manager.next()


async def on_education_entered(
    message: Message,
    widget,
    dialog_manager: DialogManager,
    value: str,
    **kwargs,
):
    dialog_manager.dialog_data["quiz_dod_education"] = value
    dialog_manager.dialog_data["quiz_dod_last_score"] = 0

    user = message.from_user
    if user:
        full_name = dialog_manager.dialog_data.get("quiz_dod_name", "")
        phone = dialog_manager.dialog_data.get("quiz_dod_phone", "")
        email = dialog_manager.dialog_data.get("quiz_dod_email", "")
        try:
            await save_user_info(
                dialog_manager,
                user.id,
                full_name=full_name,
                phone=phone,
                email=email,
                education=value,
            )
        except Exception:
            # Ошибку уже залогировали внутри save_user_info
            pass
    else:
        logger.warning("[QUIZ_DOD] Can't save user info: message.from_user missing")

    _reset_quiz_progress(dialog_manager)
    await dialog_manager.switch_to(
        QuizDodSG.QUESTIONS,
        show_mode=ShowMode.SEND,
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
        correct_answer = question.options[question.correct]
        is_correct = selected_option == question.correct

        if is_correct:
            dialog_data["quiz_dod_correct_answers"] = dialog_data.get("quiz_dod_correct_answers", 0) + 1
            feedback_text = "✅ <b>Правильный ответ!</b>"
        else:
            feedback_text = f"❌ <b>Неправильно</b>..\n\nПравильный ответ: {correct_answer}"

        await callback.message.answer(feedback_text)

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

        if dialog_data["quiz_dod_best_updated"]:
            await save_quiz_result(dialog_manager, callback.from_user.id, score)

        await callback.message.answer("""Мы очень ценим твою активность ❤️ 

В знак благодарности приготовили для тебя небольшой подарок – цифровой стикерпак с нашим маскотом 

Ниже – один из стикеров. Сохраняй скорей и используй его в чатах и комментариях – пусть все знают, что ты на стороне КБК 💪🏻""")

        await asyncio.sleep(5)

        await callback.message.answer_sticker('CAACAgIAAxkBAAETmC9pBlc9BAjTquUvcGJ0a04ZH4g6dAACwGoAAkEIMElCkBSwcWM0rDYE')

        await asyncio.sleep(2)

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