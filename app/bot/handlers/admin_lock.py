"""Admin lock handlers"""
import logging

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage

from app.utils.rbac import is_lock_mode_enabled

logger = logging.getLogger(__name__)

# Константы для Redis ключей
LOCK_KEY = "bot:lock_mode"

admin_lock_router = Router(name="admin_commands")


class AdminFilter(Filter):
    """Admin filter. Returns bool when calle. Takes admin_ids list at init"""
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        is_admin = message.from_user.id in self.admin_ids
        logger.debug("Admin filter check: user_id=%s, is_admin=%s",
                     message.from_user.id, is_admin)
        return is_admin


class NonAdminFilter(Filter):
    """Non-Admin filter. Returns bool when called. Takes admin_ids list at init"""

    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        is_non_admin = message.from_user.id not in self.admin_ids
        logger.debug("Non-admin flter check: user_id=%s, is_non_admin=%s",
                     message.from_user.id, is_non_admin)
        return is_non_admin


class NonAdminCallbackFilter(Filter):
    """Non-Admin callback filter. Returns bool when called. Takes admin_ids list at init"""

    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, callback_query: CallbackQuery) -> bool:
        is_non_admin = callback_query.from_user.id not in self.admin_ids
        logger.debug("Non-admin filter check (callback): user_id=%s, is_non_admin=%s",
                    callback_query.from_user.id, is_non_admin)
        return is_non_admin


async def set_lock_mode(storage: RedisStorage, enabled: bool) -> bool:
    """Set lock mode in Redis storage"""
    try:
        redis = storage.redis
        if enabled:
            await redis.set(LOCK_KEY, "1")
            logger.info("Lock mode is set in Redis: 1")
        else:
            await redis.set(LOCK_KEY, "0")
            logger.info("Lock mode is set in Redis: 0")
        return True
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.excpeption("Exception while setting lock mode in Redis: %s", e)
        return False


def setup_admin_lock_router(admin_ids: list[int]) -> Router: # pylint: disable=too-many-statements
    """Setup router with admin filters"""

    logger.info("Setup admin router for IDs: %s", admin_ids)

    admin_check = AdminFilter(admin_ids)
    non_admin_check = NonAdminFilter(admin_ids)
    non_admin_callback_check = NonAdminCallbackFilter(admin_ids)

    @admin_lock_router.message(Command("lock"), admin_check)
    async def cmd_lock(message: Message, state: FSMContext):
        logger.info("Admin %s executes /lock", message.from_user.id)
        storage = state.storage

        current_mode = await is_lock_mode_enabled(storage)
        logger.info("Current lock mode: %s", current_mode)

        if current_mode:
            # Режим включен - выключаем
            success = await set_lock_mode(storage, False)
            if success:
                await message.answer(
                    "� Режим блокировки выключен!\n"
                    "Все пользователи снова имеют доступ к боту."
                )
                logger.info(
                    "Админ %s выключил режим блокировки через /lock",
                    message.from_user.id,
                )
            else:
                await message.answer("❌ Ошибка при выключении режима блокировки")
        else:
            # Режим выключен - включаем
            success = await set_lock_mode(storage, True)
            if success:
                await message.answer(
                    "🔒 Lock mode is now ON!\n"
                )
                logger.warning(
                    "Admin %s activated lock mode via /lock —— LOCK MODE IS ON",
                    message.from_user.id,
                )
            else:
                await message.answer("❌ Ошибка при включении режима блокировки")

    @admin_lock_router.message(Command("unlock"), admin_check)
    async def cmd_unlock(message: Message, state: FSMContext):
        """/unlock - turns lock mode off"""
        logger.info("Админ %s выполняет команду /unlock", message.from_user.id)
        storage = state.storage

        current_mode = await is_lock_mode_enabled(storage)

        if not current_mode:
            await message.answer("🔓 Lock mode is off")
        else:
            success = await set_lock_mode(storage, False)
            if success:
                await message.answer(
                    "🔓 Lock mode is off"
                )
                logger.info("Admin %s turned OFF lock mode", message.from_user.id)
            else:
                await message.answer("❌ Error while turning lock mode off")

    @admin_lock_router.message(Command("status"), admin_check)
    async def cmd_status(message: Message, state: FSMContext):
        """/status - shows current lock status"""
        storage = state.storage

        current_mode = await is_lock_mode_enabled(storage)
        logger.info("Lock status: %s", current_mode)

        if current_mode:
            status_text = "🔒 Lock mode is ON"
        else:
            status_text = "🔓 Lock mode is OFF"

        admin_list = ", ".join(map(str, admin_ids))

        await message.answer(
            f"{status_text}\n\n"
            f"• Админы: {admin_list}\n\n"
        )

    @admin_lock_router.message(non_admin_check)
    async def handle_non_admin_message(message: Message, state: FSMContext):
        """Handle non-admin changes while on lock"""
        storage = state.storage

        lock_enabled = await is_lock_mode_enabled(storage)

        if lock_enabled:
            await message.answer(
                "🔒 Бот временно заблокирован для технических работ.\n"
                "Попробуйте позже."
            )
            logger.warning(
                "🚫 BLOCKED user %s (@%s) - lock mode is on",
                message.from_user.id,
                message.from_user.username,
            )
            return True

    @admin_lock_router.callback_query(non_admin_callback_check)
    async def handle_non_admin_callback(callback_query: CallbackQuery, state: FSMContext):
        """Перехватывает все callback'и от не-админов в режиме блокировки"""
        storage = state.storage

        lock_enabled = await is_lock_mode_enabled(storage)

        if lock_enabled:
            await callback_query.answer(
                "🔒 Бот временно заблокирован для технических работ. Попробуйте позже.",
                show_alert=True
            )
            logger.warning(
                "🚫 BLOCKED callback of user %s (@%s) - lock mode is on",
                callback_query.from_user.id,
                callback_query.from_user.username,
            )
            return True

    return admin_lock_router
