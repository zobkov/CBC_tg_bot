"""Admin lock handlers"""
import logging

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.registration.states import RegistrationSG
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
    
    @admin_lock_router.message(Command("ch_roles"), admin_check)
    async def cmd_change_roles(
        message: Message,
        db,
        user_ctx_middleware=None,
        redis=None,
        **kwargs,
    ):
        """/ch_roles - switches Staff <-> Guest"""
        logger.info(f"ADMIN {message.from_user.id} executes /ch_roles")
        
        # Get middleware и Redis from dependencies/kwargs
        user_ctx_middleware = user_ctx_middleware or kwargs.get("user_ctx_middleware")
        redis_client = redis or kwargs.get("redis")
        logger.debug(f"user_ctx_middleware получен: {user_ctx_middleware is not None}")
        logger.debug(f"redis_client получен: {redis_client is not None}")
        
        try:
            # Get current roles of a user
            current_roles = await db.users.get_user_roles(user_id=message.from_user.id)
            logger.info(f"Текущие роли админа {message.from_user.id}: {current_roles}")
            
            # Get new role (switch)
            if "staff" in current_roles:
                # Staff -> Guest
                new_roles = ["guest"]
                action = "Staff → Guest"
                emoji = "👤"
            elif "guest" in current_roles:
                # Guest -> Staff  
                new_roles = ["staff"]
                action = "Guest → Staff"
                emoji = "👥"
            else:
                # If none -> guest
                new_roles = ["guest"]
                action = "Установлена роль Guest"
                emoji = "👤"
            
            # Check if roles changed ]
            if set(new_roles) == set(current_roles):
                await message.answer(
                    f"ℹ️ Роли уже установлены правильно!\n"
                    f"📋 Текущие роли: {', '.join(new_roles)}"
                )
                return
            
            # Update roles 
            await db.users.set_user_roles(
                user_id=message.from_user.id, 
                roles=new_roles,
                granted_by=message.from_user.id
            )
            
            # User cache invalidated
            if user_ctx_middleware:
                await user_ctx_middleware.invalidate_user_cache(message.from_user.id)
                logger.info(f"Cached user role id={message.from_user.id} invalidated through middleware")
            elif redis_client:
                # Fallback: call to Redis 
                try:
                    cache_key = f"rbac:{message.from_user.id}"
                    await redis_client.delete(cache_key)
                    logger.warning(f"Cached user role id={message.from_user.id} invalidated through Redis directly. Check if middleware works properly")
                except Exception as e:
                    logger.warning(f"Ошибка инвалидации кэша через Redis: {e}")
            else:
                logger.error("RBAC ERROR. Middleware are Redis unavailable, user chache is not invalidated")
            
            # Формируем ответ
            roles_text = ", ".join(new_roles)
            await message.answer(
                f"{emoji} Roles changed\n\n"
                f"🔄 Action: {action}\n"
                f"📋 New roles: {roles_text}\n\n"
                f"ℹ️ Reset by /menu"
            )
            
            logger.info(f"ADMIN id={message.from_user.id} changed their roles: {current_roles} → {new_roles}")
            
        except Exception as e:
            logger.error(f"ERROR while chaning admin roles ADMIN id={message.from_user.id}: {e}")
            await message.answer(
                "❌ ERORR while changing roles\n"
                "/start"
            )

    @admin_lock_router.message(Command("sync_google"))
    async def sync_google_command(message: Message, db=None):
        """Синхронизация креативных заявок с Google Sheets"""
        if not db:
            await message.answer("❌ Ошибка доступа к базе данных")
            return

        try:
            from app.services.creative_google_sync import CreativeGoogleSheetsSync

            await message.answer("⏳ Запускаю синхронизацию с Google Sheets...")

            sync_service = CreativeGoogleSheetsSync(db)
            count = await sync_service.sync_all_applications()

            await message.answer(f"✅ Синхронизировано {count} креативных заявок")

            logger.info(
                f"[ADMIN] Google Sheets manual sync completed by user {message.from_user.id}, "
                f"synced {count} applications"
            )

        except FileNotFoundError:
            await message.answer(
                "❌ Файл credentials не найден. Проверьте конфигурацию Google Sheets."
            )
            logger.error("Google credentials file not found during manual sync")
        except Exception as e:
            logger.error(f"Error during manual Google Sheets sync: {e}", exc_info=True)
            await message.answer(f"❌ Ошибка синхронизации: {str(e)}")

    @admin_lock_router.message(Command("force_start"), admin_check)
    async def cmd_force_start(message: Message, dialog_manager: DialogManager):
        """Принудительно запускает диалог регистрации"""
        logger.info(f"ADMIN {message.from_user.id} executes /force_start")
        
        try:
            await dialog_manager.start(
                state=RegistrationSG.MAIN,
                mode=StartMode.RESET_STACK
            )
            logger.info(f"Registration dialog forcefully started for user {message.from_user.id}")
        except Exception as e:
            logger.error(f"Error starting registration dialog: {e}", exc_info=True)
            await message.answer(f"❌ Ошибка при запуске регистрации: {str(e)}")

    # RETURN ROUTER !!!
    return admin_lock_router
