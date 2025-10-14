"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters.rbac import IsNotBanned

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
# router.message.filter(IsNotBanned())
# router.callback_query.filter(IsNotBanned())


# Убираем обработчики /start и /menu - теперь они обрабатываются диалогами


@router.message(Command("help"))
async def help_command(message: Message, roles: set[str] = None):
    """Справочная информация по ролям"""
    roles = roles or set()
    
    base_help = (
        "📖 <b>Справка по боту КБК</b>\n\n"
        "Основные команды:\n"
        "• /start, /menu - Главное меню\n"
        "• /help - Эта справка\n"
        "• /whoami - Информация о вас\n\n"
    )
    
    if "admin" in roles:
        admin_help = (
            "🔧 <b>Команды администратора:</b>\n"
            "• /grant <role> - Выдать роль (в ответ на сообщение)\n"
            "• /revoke <role> - Отозвать роль\n"
            "• /grant <role> <user_id> - Выдать роль по ID\n"
            "• /revoke <role> <user_id> - Отозвать роль по ID\n\n"
            "Доступные роли: admin, staff, volunteer, guest, banned\n\n"
        )
        await message.answer(base_help + admin_help)
    elif "staff" in roles:
        staff_help = (
            "👔 <b>Функции сотрудника:</b>\n"
            "• Работа с заявками участников\n"
            "• Модерация контента\n"
            "• Техническая поддержка\n\n"
        )
        await message.answer(base_help + staff_help)
    elif "volunteer" in roles:
        volunteer_help = (
            "🤝 <b>Функции волонтёра:</b>\n"
            "• Помощь новым участникам\n"
            "• Ответы на частые вопросы\n"
            "• Информационная поддержка\n\n"
        )
        await message.answer(base_help + volunteer_help)
    else:
        guest_help = (
            "🎯 <b>Возможности участника:</b>\n"
            "• Подача заявки на участие в КБК\n"
            "• Выполнение тестовых заданий\n"
            "• Отслеживание статуса заявки\n\n"
            "Для начала работы нажмите /start\n\n"
        )
        await message.answer(base_help + guest_help)


@router.message(Command("whoami"))
async def whoami_command(message: Message, current_user=None, roles: set[str] = None):
    """Информация о пользователе и его ролях"""
    roles = roles or set()
    user_id = message.from_user.id
    username = message.from_user.username or "не установлен"
    
    roles_list = ", ".join(sorted(roles)) if roles else "нет ролей"
    
    info_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Username: @{username}\n"
        f"🏷 Роли: {roles_list}\n"
    )
    
    if current_user:
        # Проверяем, является ли created строкой или datetime объектом
        if hasattr(current_user.created, 'strftime'):
            created_str = current_user.created.strftime('%d.%m.%Y %H:%M')
        else:
            created_str = str(current_user.created)
            
        info_text += (
            f"📅 Регистрация: {created_str}\n"
            f"🌐 Язык: {current_user.language}\n"
            f"📊 Статус заявки: {current_user.submission_status}\n"
        )
    
    await message.answer(info_text)


# Debug handler в самом конце, чтобы не блокировать другие команды
@router.message()
async def debug_all_messages(message: Message):
    """Debug: все сообщения"""
    # Если сообщение не обработано другими хендлерами, отвечаем
    if message.text and message.text.startswith('/'):
        await message.answer(f"❓ Команда '{message.text}' не распознана. Используйте /help для справки.")