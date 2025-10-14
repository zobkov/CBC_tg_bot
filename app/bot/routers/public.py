"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router, F
from aiogram.types import Message

from app.bot.filters.rbac import IsNotBanned

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
router.message.filter(IsNotBanned())
router.callback_query.filter(IsNotBanned())


@router.message(F.text.in_(["/start", "/menu"]))
async def start_command(message: Message, roles: set[str] = None):
    """
    Обработчик команды /start и /menu
    Перенаправляет пользователей в соответствующие разделы по ролям
    """
    roles = roles or set()
    user_id = message.from_user.id
    
    logger.info(f"Start command from user {user_id} with roles: {list(roles)}")
    
    # Определяем наивысшую роль пользователя для перенаправления
    if "admin" in roles:
        await message.answer(
            "🔧 <b>Панель администратора КБК</b>\n\n"
            "Добро пожаловать в административную панель системы отбора команды КБК.\n\n"
            "Доступные функции:\n"
            "• Управление пользователями и ролями\n"
            "• Просмотр статистики\n"
            "• Системные настройки\n\n"
            "Для получения справки используйте /help"
        )
    elif "staff" in roles:
        await message.answer(
            "👔 <b>Кабинет сотрудника КБК</b>\n\n"
            "Добро пожаловать в рабочий кабинет сотрудника КБК.\n\n"
            "Доступные функции:\n"
            "• Работа с заявками\n"
            "• Поддержка пользователей\n"
            "• Отчеты и аналитика\n\n"
            "Для получения справки используйте /help"
        )
    elif "volunteer" in roles:
        await message.answer(
            "🤝 <b>Кабинет волонтёра КБК</b>\n\n"
            "Добро пожаловать в кабинет волонтёра КБК.\n\n"
            "Доступные функции:\n"
            "• Помощь пользователям\n"
            "• Базовая поддержка\n"
            "• Информация о мероприятии\n\n"
            "Для получения справки используйте /help"
        )
    else:  # guest и остальные
        await message.answer(
            "🎯 <b>Личный кабинет участника КБК</b>\n\n"
            "Добро пожаловать в систему отбора команды КБК!\n\n"
            "Доступные функции:\n"
            "• Подача заявки на участие\n"
            "• Отслеживание статуса заявки\n"
            "• Выполнение заданий\n"
            "• Получение уведомлений\n\n"
            "Для получения справки используйте /help"
        )


@router.message(F.text == "/help")
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


@router.message(F.text == "/whoami")
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
        info_text += (
            f"📅 Регистрация: {current_user.created.strftime('%d.%m.%Y %H:%M')}\n"
            f"🌐 Язык: {current_user.language}\n"
            f"📊 Статус заявки: {current_user.submission_status}\n"
        )
    
    await message.answer(info_text)