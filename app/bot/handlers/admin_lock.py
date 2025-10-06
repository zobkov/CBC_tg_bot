"""
Команды для управления админской блокировкой
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.bot.middlewares.admin_lock import set_lock_mode, is_lock_mode_enabled

logger = logging.getLogger(__name__)

# Создаем роутер для админских команд
admin_commands_router = Router(name="admin_commands")


class AdminFilter:
    """Фильтр для проверки админов"""
    
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = set(admin_ids)
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


def setup_admin_commands_router(admin_ids: list[int]) -> Router:
    """Настраивает роутер с админскими командами"""
    
    logger.info(f"Настройка админских команд для ID: {admin_ids}")
    
    admin_check = AdminFilter(admin_ids)
    
    @admin_commands_router.message(Command("lock"), admin_check)
    async def cmd_lock(message: Message, state: FSMContext):
        """Команда /lock - переключает режим блокировки для не-админов"""
        logger.info(f"Админ {message.from_user.id} выполняет команду /lock")
        storage = state.storage
        
        current_mode = await is_lock_mode_enabled(storage)
        logger.info(f"Текущий режим блокировки: {current_mode}")
        
        if current_mode:
            # Режим включен - выключаем
            success = await set_lock_mode(storage, False)
            if success:
                await message.answer(
                    "🔓 Режим блокировки выключен!\n"
                    "Все пользователи снова имеют доступ к боту."
                )
                logger.info(f"Админ {message.from_user.id} выключил режим блокировки через /lock")
            else:
                await message.answer("❌ Ошибка при выключении режима блокировки")
        else:
            # Режим выключен - включаем
            success = await set_lock_mode(storage, True)
            if success:
                await message.answer(
                    "🔒 Режим блокировки включен!\n"
                    "Все пользователи (кроме админов) заблокированы."
                )
                logger.info(f"Админ {message.from_user.id} включил режим блокировки через /lock")
            else:
                await message.answer("❌ Ошибка при включении режима блокировки")
    
    @admin_commands_router.message(Command("unlock"), admin_check)
    async def cmd_unlock(message: Message, state: FSMContext):
        """Команда /unlock - выключает режим блокировки"""
        logger.info(f"Админ {message.from_user.id} выполняет команду /unlock")
        storage = state.storage
        
        current_mode = await is_lock_mode_enabled(storage)
        
        if not current_mode:
            await message.answer(
                "🔓 Режим блокировки уже выключен!\n"
                "Все пользователи имеют доступ к боту."
            )
        else:
            success = await set_lock_mode(storage, False)
            if success:
                await message.answer(
                    "🔓 Режим блокировки выключен!\n"
                    "Все пользователи снова имеют доступ к боту."
                )
                logger.info(f"Админ {message.from_user.id} выключил режим блокировки")
            else:
                await message.answer("❌ Ошибка при выключении режима блокировки")
    
    @admin_commands_router.message(Command("status"), admin_check)
    async def cmd_status(message: Message, state: FSMContext):
        """Команда /status - показывает текущий статус блокировки"""
        logger.info(f"Админ {message.from_user.id} проверяет статус блокировки")
        storage = state.storage
        
        current_mode = await is_lock_mode_enabled(storage)
        logger.info(f"Статус блокировки: {current_mode}")
        
        if current_mode:
            status_text = "🔒 Режим блокировки ВКЛЮЧЕН"
            details = "Все не-админы заблокированы"
        else:
            status_text = "🔓 Режим блокировки ВЫКЛЮЧЕН"
            details = "Все пользователи имеют доступ"
        
        admin_list = ", ".join(map(str, admin_ids))
        
        await message.answer(
            f"{status_text}\n\n"
            f"📊 Детали:\n"
            f"• {details}\n"
            f"• Админы: {admin_list}\n\n"
            f"📋 Доступные команды:\n"
            f"• /lock - переключить блокировку\n"
            f"• /unlock - принудительно выключить блокировку\n"
            f"• /status - статус системы"
        )
    
    return admin_commands_router

import logging
from typing import Any
from aiogram import Router, F
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage

logger = logging.getLogger(__name__)

# Создаем роутер с высоким приоритетом для админской системы
admin_lock_router = Router(name="admin_lock")

# Константы для Redis ключей
LOCK_KEY = "bot:lock_mode"


class AdminFilter(Filter):
    """Фильтр для проверки админских прав"""
    
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids
    
    async def __call__(self, message: Message) -> bool:
        """Проверяет, является ли пользователь админом"""
        is_admin = message.from_user.id in self.admin_ids
        logger.debug(f"Проверка админа: user_id={message.from_user.id}, is_admin={is_admin}")
        return is_admin


class NonAdminFilter(Filter):
    """Фильтр для не-админов"""
    
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids
    
    async def __call__(self, message: Message) -> bool:
        """Проверяет, что пользователь НЕ админ"""
        is_non_admin = message.from_user.id not in self.admin_ids
        logger.debug(f"Проверка не-админа: user_id={message.from_user.id}, is_non_admin={is_non_admin}")
        return is_non_admin


class NonAdminCallbackFilter(Filter):
    """Фильтр для callback'ов от не-админов"""
    
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids
    
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        """Проверяет, что пользователь НЕ админ"""
        is_non_admin = callback_query.from_user.id not in self.admin_ids
        logger.debug(f"Проверка не-админа (callback): user_id={callback_query.from_user.id}, is_non_admin={is_non_admin}")
        return is_non_admin


async def is_lock_mode_enabled(storage: RedisStorage) -> bool:
    """Проверяет, включен ли режим блокировки"""
    try:
        redis = storage.redis
        result = await redis.get(LOCK_KEY)
        logger.debug(f"Значение в Redis для ключа {LOCK_KEY}: {result} (тип: {type(result)})")
        # Redis возвращает bytes, сравниваем с b"1"
        is_enabled = result == b"1" if result else False
        logger.debug(f"Режим блокировки включен: {is_enabled}")
        return is_enabled
    except Exception as e:
        logger.error(f"Ошибка при проверке режима блокировки: {e}")
        return False


async def set_lock_mode(storage: RedisStorage, enabled: bool) -> bool:
    """Устанавливает режим блокировки"""
    try:
        redis = storage.redis
        if enabled:
            await redis.set(LOCK_KEY, "1")
            logger.info("Режим блокировки установлен в Redis: 1")
        else:
            await redis.set(LOCK_KEY, "0")
            logger.info("Режим блокировки установлен в Redis: 0")
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке режима блокировки: {e}")
        return False


def setup_admin_lock_router(admin_ids: list[int]) -> Router:
    """Настраивает роутер с админскими фильтрами"""
    
    logger.info(f"Настройка админского роутера для ID: {admin_ids}")
    
    admin_check = AdminFilter(admin_ids)
    non_admin_check = NonAdminFilter(admin_ids)
    non_admin_callback_check = NonAdminCallbackFilter(admin_ids)
    
    @admin_lock_router.message(Command("lock"), admin_check)
    async def cmd_lock(message: Message, state: FSMContext):
        """Команда /lock - переключает режим блокировки для не-админов"""
        logger.info(f"Админ {message.from_user.id} выполняет команду /lock")
        storage = state.storage
        
        current_mode = await is_lock_mode_enabled(storage)
        logger.info(f"Текущий режим блокировки: {current_mode}")
        
        if current_mode:
            # Режим включен - выключаем
            success = await set_lock_mode(storage, False)
            if success:
                await message.answer(
                    "� Режим блокировки выключен!\n"
                    "Все пользователи снова имеют доступ к боту."
                )
                logger.info(f"Админ {message.from_user.id} выключил режим блокировки через /lock")
            else:
                await message.answer("❌ Ошибка при выключении режима блокировки")
        else:
            # Режим выключен - включаем
            success = await set_lock_mode(storage, True)
            if success:
                await message.answer(
                    "🔒 Режим блокировки включен!\n"
                    "Все пользователи (кроме админов) заблокированы."
                )
                logger.info(f"Админ {message.from_user.id} включил режим блокировки через /lock")
            else:
                await message.answer("❌ Ошибка при включении режима блокировки")
    
    @admin_lock_router.message(Command("unlock"), admin_check)
    async def cmd_unlock(message: Message, state: FSMContext):
        """Команда /unlock - выключает режим блокировки"""
        logger.info(f"Админ {message.from_user.id} выполняет команду /unlock")
        storage = state.storage
        
        current_mode = await is_lock_mode_enabled(storage)
        
        if not current_mode:
            await message.answer(
                "🔓 Режим блокировки уже выключен!\n"
                "Все пользователи имеют доступ к боту."
            )
        else:
            success = await set_lock_mode(storage, False)
            if success:
                await message.answer(
                    "🔓 Режим блокировки выключен!\n"
                    "Все пользователи снова имеют доступ к боту."
                )
                logger.info(f"Админ {message.from_user.id} выключил режим блокировки")
            else:
                await message.answer("❌ Ошибка при выключении режима блокировки")
    
    @admin_lock_router.message(Command("status"), admin_check)
    async def cmd_status(message: Message, state: FSMContext):
        """Команда /status - показывает текущий статус блокировки"""
        logger.info(f"Админ {message.from_user.id} проверяет статус блокировки")
        storage = state.storage
        
        current_mode = await is_lock_mode_enabled(storage)
        logger.info(f"Статус блокировки: {current_mode}")
        
        if current_mode:
            status_text = "🔒 Режим блокировки ВКЛЮЧЕН"
            details = "Все не-админы заблокированы"
        else:
            status_text = "🔓 Режим блокировки ВЫКЛЮЧЕН"
            details = "Все пользователи имеют доступ"
        
        admin_list = ", ".join(map(str, admin_ids))
        
        await message.answer(
            f"{status_text}\n\n"
            f"📊 Детали:\n"
            f"• {details}\n"
            f"• Админы: {admin_list}\n\n"
            f"📋 Доступные команды:\n"
            f"• /lock - переключить блокировку\n"
            f"• /unlock - принудительно выключить блокировку\n"
            f"• /status - статус системы"
        )
    
    @admin_lock_router.message(non_admin_check)
    async def handle_non_admin_message(message: Message, state: FSMContext):
        """Перехватывает все сообщения от не-админов в режиме блокировки"""
        storage = state.storage
        
        lock_enabled = await is_lock_mode_enabled(storage)
        logger.info(f"Сообщение от не-админа {message.from_user.id} (@{message.from_user.username}), режим блокировки: {lock_enabled}")
        
        if lock_enabled:
            await message.answer(
                "🔒 Бот временно заблокирован для технических работ.\n"
                "Попробуйте позже."
            )
            logger.warning(f"🚫 ЗАБЛОКИРОВАН доступ пользователя {message.from_user.id} (@{message.from_user.username}) - режим блокировки включен")
            # Возвращаем True, чтобы остановить обработку других хендлеров
            return True
        else:
            logger.debug(f"✅ Пропускаем сообщение от не-админа {message.from_user.id} - режим блокировки выключен")
    
    @admin_lock_router.callback_query(non_admin_callback_check)
    async def handle_non_admin_callback(callback_query: CallbackQuery, state: FSMContext):
        """Перехватывает все callback'и от не-админов в режиме блокировки"""
        storage = state.storage
        
        lock_enabled = await is_lock_mode_enabled(storage)
        logger.info(f"Callback от не-админа {callback_query.from_user.id} (@{callback_query.from_user.username}), режим блокировки: {lock_enabled}")
        
        if lock_enabled:
            await callback_query.answer(
                "🔒 Бот временно заблокирован для технических работ. Попробуйте позже.",
                show_alert=True
            )
            logger.warning(f"🚫 ЗАБЛОКИРОВАН callback пользователя {callback_query.from_user.id} (@{callback_query.from_user.username}) - режим блокировки включен")
            return True
        else:
            logger.debug(f"✅ Пропускаем callback от не-админа {callback_query.from_user.id} - режим блокировки выключен")
    
    return admin_lock_router