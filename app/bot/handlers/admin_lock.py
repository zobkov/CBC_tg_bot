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

from app.bot.filters.admin import AdminFilter

logger = logging.getLogger(__name__)

# Константы для Redis ключей
LOCK_KEY = "bot:lock_mode"


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
    admin_lock_router = Router(name="admin_commands")

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
            from app.services.creative_google_sync import CreativeGoogleSheetsSyncPart2

            await message.answer("⏳ Запускаю синхронизацию второго этапа с Google Sheets...")

            sync_service = CreativeGoogleSheetsSyncPart2(db)
            count = await sync_service.sync_all_applications()

            await message.answer(f"✅ Синхронизировано {count} заявок второго этапа")

            logger.info(
                f"[ADMIN] Google Sheets part2 sync completed by user {message.from_user.id}, "
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

    @admin_lock_router.message(Command("grant_gsom"), admin_check)
    async def cmd_grant_gsom(message: Message, db=None) -> None:
        """/grant_gsom <user_id> <1|0> [mentor_contacts] — add/remove user from GSOM branch."""
        logger.info("ADMIN %d executes /grant_gsom", message.from_user.id)

        if not db:
            await message.answer("❌ DB недоступна")
            return

        parts = (message.text or "").split(maxsplit=3)
        if len(parts) < 3:
            await message.answer(
                "Использование: /grant_gsom &lt;user_id&gt; &lt;1|0&gt; [mentor_contacts]\n"
                "1 — добавить в GSOM-ветку, 0 — удалить\n"
                "Примеры:\n"
                "/grant_gsom 123456789 1 @ivanov_mentor\n"
                "/grant_gsom 123456789 0"
            )
            return

        raw_user_id = parts[1]
        raw_flag = parts[2]
        mentor_contacts = parts[3] if len(parts) == 4 else None

        try:
            target_user_id = int(raw_user_id)
        except ValueError:
            await message.answer(f"❌ Неверный user_id: {raw_user_id!r}")
            return

        if raw_flag not in ("0", "1"):
            await message.answer("❌ Флаг должен быть 1 (добавить) или 0 (удалить)")
            return

        try:
            if raw_flag == "0":
                deleted = await db.user_mentors.delete_by_user_id(user_id=target_user_id)
                if deleted:
                    await message.answer(
                        f"✅ Пользователь {target_user_id} удалён из GSOM-ветки."
                    )
                else:
                    await message.answer(
                        f"ℹ️ Пользователь {target_user_id} не был в GSOM-ветке."
                    )
                logger.info(
                    "ADMIN %d revoked GSOM access for user %d (deleted=%s)",
                    message.from_user.id, target_user_id, deleted,
                )
            else:
                await db.user_mentors.upsert(
                    user_id=target_user_id,
                    mentor_contacts=mentor_contacts,
                )
                contacts_info = f"\nМентор: {mentor_contacts}" if mentor_contacts else ""
                await message.answer(
                    f"✅ Пользователь {target_user_id} добавлен в GSOM-ветку.{contacts_info}\n"
                    "Теперь при входе в раздел «Гранты» ему откроется личный кабинет ВШМ."
                )
                logger.info(
                    "ADMIN %d granted GSOM access to user %d (mentor: %s)",
                    message.from_user.id, target_user_id, mentor_contacts,
                )
        except Exception as exc:
            logger.error("grant_gsom failed: %s", exc, exc_info=True)
            await message.answer(f"❌ Ошибка: {exc}")

    @admin_lock_router.message(Command("config_reset"), admin_check)
    async def cmd_config_reset(message: Message) -> None:
        """/config_reset — force-reload grant_lessons.json from disk."""
        logger.info("ADMIN %d executes /config_reset", message.from_user.id)
        try:
            from app.services.grant_lessons_config import load_grant_lessons
            lessons = load_grant_lessons(force=True)
            await message.answer(
                f"✅ Grant lessons config reloaded: {len(lessons)} lessons."
            )
        except Exception as exc:
            logger.error("config_reset failed: %s", exc, exc_info=True)
            await message.answer(f"❌ Ошибка при перезагрузке конфига: {exc}")

    @admin_lock_router.message(Command("grant_lesson"), admin_check)
    async def cmd_grant_lesson(message: Message, db=None) -> None:
        """/grant_lesson <user_id> <lesson_tag> <1|0> — lock/unlock a lesson for a user."""
        logger.info("ADMIN %d executes /grant_lesson", message.from_user.id)

        if not db:
            await message.answer("❌ DB недоступна")
            return

        parts = (message.text or "").split()
        if len(parts) != 4:
            await message.answer(
                "Использование: /grant_lesson &lt;user_id&gt; &lt;lesson_tag&gt; &lt;1|0&gt;\n"
                "1 — открыть урок, 0 — закрыть\n"
                "Примеры:\n"
                "/grant_lesson 123456789 lesson_1 1\n"
                "/grant_lesson 123456789 lesson_1 0"
            )
            return

        _, raw_user_id, tag, raw_flag = parts
        try:
            target_user_id = int(raw_user_id)
        except ValueError:
            await message.answer(f"❌ Неверный user_id: {raw_user_id!r}")
            return

        if raw_flag not in ("0", "1"):
            await message.answer("❌ Флаг должен быть 1 (открыть) или 0 (закрыть)")
            return

        try:
            from app.services.grant_lessons_config import get_lesson_by_tag
            lesson = get_lesson_by_tag(tag)
            if lesson is None:
                await message.answer(
                    f"❌ Тег '{tag}' не найден в grant_lessons.json.\n"
                    "Проверьте тег или выполните /config_reset."
                )
                return

            record = await db.user_mentors.get_by_user_id(user_id=target_user_id)
            if record is None:
                await message.answer(
                    f"❌ Пользователь {target_user_id} не найден в таблице user_mentors.\n"
                    "Сначала добавьте его через /grant_gsom."
                )
                return

            lesson_name = lesson.get("name", tag)
            if raw_flag == "1":
                added = await db.user_mentors.approve_lesson(
                    user_id=target_user_id, tag=tag
                )
                if added:
                    await message.answer(
                        f"✅ Урок «{lesson_name}» открыт для пользователя {target_user_id}."
                    )
                    logger.info(
                        "ADMIN %d unlocked lesson '%s' for user %d",
                        message.from_user.id, tag, target_user_id,
                    )
                else:
                    await message.answer(
                        f"ℹ️ Урок «{lesson_name}» уже был открыт для пользователя {target_user_id}."
                    )
            else:
                removed = await db.user_mentors.revoke_lesson(
                    user_id=target_user_id, tag=tag
                )
                if removed:
                    await message.answer(
                        f"✅ Урок «{lesson_name}» закрыт для пользователя {target_user_id}."
                    )
                    logger.info(
                        "ADMIN %d locked lesson '%s' for user %d",
                        message.from_user.id, tag, target_user_id,
                    )
                else:
                    await message.answer(
                        f"ℹ️ Урок «{lesson_name}» и так был закрыт для пользователя {target_user_id}."
                    )
        except Exception as exc:
            logger.error("grant_lesson failed: %s", exc, exc_info=True)
            await message.answer(f"❌ Ошибка: {exc}")

    @admin_lock_router.message(Command("grant_status"), admin_check)
    async def cmd_grant_status(message: Message, db=None) -> None:
        """/grant_status <user_id> — show GSOM grant status for a user."""
        logger.info("ADMIN %d executes /grant_status", message.from_user.id)

        if not db:
            await message.answer("❌ DB недоступна")
            return

        parts = (message.text or "").split()
        if len(parts) != 2:
            await message.answer(
                "Использование: /grant_status &lt;user_id&gt;\n"
                "Пример: /grant_status 123456789"
            )
            return

        try:
            target_user_id = int(parts[1])
        except ValueError:
            await message.answer(f"❌ Неверный user_id: {parts[1]!r}")
            return

        try:
            record = await db.user_mentors.get_by_user_id(user_id=target_user_id)
            if record is None:
                await message.answer(
                    f"ℹ️ Пользователь <code>{target_user_id}</code> не в GSOM-ветке."
                )
                return

            from app.services.grant_lessons_config import load_grant_lessons
            lessons = load_grant_lessons()
            approved_set = set(record.lessons_approved or [])

            mentor_line = record.mentor_contacts or "не назначен"

            if approved_set:
                lesson_lines = []
                for lesson in lessons:
                    tag = lesson.get("tag", "")
                    name = lesson.get("name", tag)
                    status = "✅" if tag in approved_set else "🔒"
                    lesson_lines.append(f"  {status} <code>{tag}</code> — {name}")
                # approved tags not present in config
                config_tags = {l.get("tag") for l in lessons}
                for tag in sorted(approved_set - config_tags):
                    lesson_lines.append(f"  ✅ <code>{tag}</code> — (не в конфиге)")
                lessons_text = "\n".join(lesson_lines)
            else:
                lesson_lines = []
                for lesson in lessons:
                    tag = lesson.get("tag", "")
                    name = lesson.get("name", tag)
                    lesson_lines.append(f"  🔒 <code>{tag}</code> — {name}")
                lessons_text = "\n".join(lesson_lines)

            await message.answer(
                f"<b>Grant status — <code>{target_user_id}</code></b>\n\n"
                f"👨‍🏫 Ментор: {mentor_line}\n"
                f"📚 Открытые уроки ({len(approved_set)}/11):\n"
                f"{lessons_text}"
            )
        except Exception as exc:
            logger.error("grant_status failed: %s", exc, exc_info=True)
            await message.answer(f"❌ Ошибка: {exc}")

    # RETURN ROUTER !!!
    return admin_lock_router
