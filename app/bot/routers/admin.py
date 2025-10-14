"""
Роутер для администраторов
"""
import logging
import re
from aiogram import Router, F
from aiogram.types import Message

from app.bot.filters.rbac import HasRole
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="admin")

# Фильтр только для админов
router.message.filter(HasRole(Role.ADMIN))
router.callback_query.filter(HasRole(Role.ADMIN))


@router.message(F.text == "/admin_panel")
async def admin_panel_command(message: Message):
    """Административная панель"""
    await message.answer(
        "🔧 <b>Панель администратора КБК</b>\n\n"
        "🔑 <b>Управление ролями:</b>\n"
        "• /grant <role> - Выдать роль (ответ на сообщение)\n"
        "• /revoke <role> - Отозвать роль\n"
        "• /grant <role> <user_id> - Выдать роль по ID\n"
        "• /revoke <role> <user_id> - Отозвать роль по ID\n\n"
        "📊 <b>Системная информация:</b>\n"
        "• /system_stats - Статистика системы\n"
        "• /active_users - Активные пользователи\n"
        "• /error_log - Последние ошибки\n\n"
        "⚙️ <b>Настройки:</b>\n"
        "• /maintenance - Режим обслуживания\n"
        "• /cache_clear - Очистить кэш\n"
        "• /backup - Создать резервную копию\n\n"
        "Доступные роли: admin, staff, volunteer, guest, banned"
    )


@router.message(F.text.regexp(r"^/grant\s+(\w+)(?:\s+(\d+))?$"))
async def grant_role_command(message: Message, db=None, redis=None):
    """Команда выдачи ролей"""
    if not db:
        await message.answer("❌ Ошибка доступа к базе данных")
        return
    
    # Парсим команду
    match = re.match(r"^/grant\s+(\w+)(?:\s+(\d+))?$", message.text.strip())
    if not match:
        await message.answer("❌ Неверный формат команды")
        return
    
    role, target_id = match.groups()
    
    # Проверяем валидность роли
    if not Role.is_valid_role(role):
        await message.answer(
            f"❌ Неизвестная роль: {role}\n"
            f"Доступные роли: {', '.join(Role.get_all_roles())}"
        )
        return
    
    # Определяем целевого пользователя
    if not target_id:
        if message.reply_to_message and message.reply_to_message.from_user:
            target_id = str(message.reply_to_message.from_user.id)
        else:
            await message.answer(
                "❌ Укажите ID пользователя или сделайте ответ на его сообщение\n"
                "Пример: /grant staff 123456789"
            )
            return
    
    try:
        target_user_id = int(target_id)
        
        # Проверяем существование пользователя
        target_user = await db.users.get_user_record(user_id=target_user_id)
        if not target_user:
            await message.answer(f"❌ Пользователь {target_user_id} не найден в системе")
            return
        
        # Проверяем, есть ли уже такая роль
        if await db.users.user_has_role(user_id=target_user_id, role=role):
            await message.answer(f"⚠️ У пользователя {target_user_id} уже есть роль '{role}'")
            return
        
        # Выдаём роль
        await db.users.add_user_role(
            user_id=target_user_id, 
            role=role, 
            granted_by=message.from_user.id
        )
        
        # Инвалидируем кэш пользователя
        if redis:
            await redis.delete(f"rbac:{target_user_id}")
        
        await message.answer(
            f"✅ Роль '{role}' успешно выдана пользователю {target_user_id}"
        )
        
        logger.info(
            f"Role granted: {role} to user {target_user_id} by admin {message.from_user.id}"
        )
        
    except ValueError:
        await message.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        logger.error(f"Error granting role: {e}")
        await message.answer(f"❌ Ошибка при выдаче роли: {e}")


@router.message(F.text.regexp(r"^/revoke\s+(\w+)(?:\s+(\d+))?$"))
async def revoke_role_command(message: Message, db=None, redis=None):
    """Команда отзыва ролей"""
    if not db:
        await message.answer("❌ Ошибка доступа к базе данных")
        return
    
    # Парсим команду
    match = re.match(r"^/revoke\s+(\w+)(?:\s+(\d+))?$", message.text.strip())
    if not match:
        await message.answer("❌ Неверный формат команды")
        return
    
    role, target_id = match.groups()
    
    # Проверяем валидность роли
    if not Role.is_valid_role(role):
        await message.answer(
            f"❌ Неизвестная роль: {role}\n"
            f"Доступные роли: {', '.join(Role.get_all_roles())}"
        )
        return
    
    # Определяем целевого пользователя
    if not target_id:
        if message.reply_to_message and message.reply_to_message.from_user:
            target_id = str(message.reply_to_message.from_user.id)
        else:
            await message.answer(
                "❌ Укажите ID пользователя или сделайте ответ на его сообщение\n"
                "Пример: /revoke staff 123456789"
            )
            return
    
    try:
        target_user_id = int(target_id)
        
        # Проверяем существование пользователя
        target_user = await db.users.get_user_record(user_id=target_user_id)
        if not target_user:
            await message.answer(f"❌ Пользователь {target_user_id} не найден в системе")
            return
        
        # Проверяем, есть ли такая роль
        if not await db.users.user_has_role(user_id=target_user_id, role=role):
            await message.answer(f"⚠️ У пользователя {target_user_id} нет роли '{role}'")
            return
        
        # Запрещаем отзывать роль admin у самого себя
        if role == Role.ADMIN.value and target_user_id == message.from_user.id:
            await message.answer("❌ Нельзя отозвать роль admin у самого себя")
            return
        
        # Отзываем роль
        await db.users.remove_user_role(
            user_id=target_user_id, 
            role=role, 
            revoked_by=message.from_user.id
        )
        
        # Инвалидируем кэш пользователя
        if redis:
            await redis.delete(f"rbac:{target_user_id}")
        
        await message.answer(
            f"✅ Роль '{role}' успешно отозвана у пользователя {target_user_id}"
        )
        
        logger.info(
            f"Role revoked: {role} from user {target_user_id} by admin {message.from_user.id}"
        )
        
    except ValueError:
        await message.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        logger.error(f"Error revoking role: {e}")
        await message.answer(f"❌ Ошибка при отзыве роли: {e}")


@router.message(F.text == "/system_stats")
async def system_stats_command(message: Message, db=None):
    """Системная статистика"""
    if not db:
        await message.answer("❌ Ошибка доступа к базе данных")
        return
    
    try:
        # TODO: Реализовать получение системной статистики
        await message.answer(
            "📊 <b>Системная статистика</b>\n\n"
            "В разработке...\n\n"
            "Будет показывать:\n"
            "• Общее количество пользователей\n"
            "• Распределение по ролям\n"
            "• Активность за период\n"
            "• Использование ресурсов\n"
            "• Статистика ошибок"
        )
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        await message.answer("❌ Ошибка при получении системной статистики")


@router.message(F.text == "/cache_clear")
async def cache_clear_command(message: Message, redis=None):
    """Очистка кэша"""
    if not redis:
        await message.answer("❌ Redis недоступен")
        return
    
    try:
        # Очищаем кэш ролей
        keys = await redis.keys("rbac:*")
        if keys:
            await redis.delete(*keys)
            await message.answer(f"✅ Очищено {len(keys)} записей кэша ролей")
        else:
            await message.answer("ℹ️ Кэш ролей уже пуст")
        
        logger.info(f"Cache cleared by admin {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        await message.answer(f"❌ Ошибка при очистке кэша: {e}")


@router.message()
async def admin_unknown_command(message: Message):
    """Обработчик неизвестных админ команд"""
    await message.answer(
        "❓ <b>Неизвестная команда</b>\n\n"
        "Доступные команды администратора:\n"
        "• /admin_panel - Панель управления\n"
        "• /grant <role> [user_id] - Выдать роль\n"
        "• /revoke <role> [user_id] - Отозвать роль\n"
        "• /system_stats - Системная статистика\n"
        "• /cache_clear - Очистить кэш\n\n"
        "Для полного списка используйте /admin_panel"
    )