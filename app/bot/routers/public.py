"""
Публичный роутер для команд, доступных всем пользователям
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.guest.states import GuestMenuSG
from app.bot.dialogs.volunteer.states import VolunteerMenuSG  
from app.bot.dialogs.staff.states import StaffMenuSG
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="public")

# Фильтруем только не заблокированных пользователей
# router.message.filter(IsNotBanned())
# router.callback_query.filter(IsNotBanned())


@router.message(Command("start"))
async def start_command(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """Команда /start - запуск диалога приветствия в зависимости от роли"""
    roles = roles or set()
    
    # Определяем состояние диалога в зависимости от роли пользователя
    if Role.ADMIN.value in roles or Role.STAFF.value in roles:
        await dialog_manager.start(state=StaffMenuSG.MAIN, mode=StartMode.RESET_STACK)
    elif Role.VOLUNTEER.value in roles:
        await dialog_manager.start(state=VolunteerMenuSG.MAIN, mode=StartMode.RESET_STACK)
    else:
        # Гости и все остальные (включая новых пользователей)
        await dialog_manager.start(state=GuestMenuSG.MAIN, mode=StartMode.RESET_STACK)


@router.message(Command("menu"))
async def menu_command(message: Message, dialog_manager: DialogManager, roles: set[str] = None):
    """Команда /menu - переход в главное меню в зависимости от роли"""
    roles = roles or set()
    
    # Определяем состояние диалога в зависимости от роли пользователя
    if Role.ADMIN.value in roles or Role.STAFF.value in roles:
        await dialog_manager.start(state=StaffMenuSG.MAIN, mode=StartMode.RESET_STACK)
    elif Role.VOLUNTEER.value in roles:
        await dialog_manager.start(state=VolunteerMenuSG.MAIN, mode=StartMode.RESET_STACK)
    else:
        # Гости и все остальные
        await dialog_manager.start(state=GuestMenuSG.MAIN, mode=StartMode.RESET_STACK)


@router.message(Command("admin_help"))
async def admin_help_command(message: Message, roles: set[str] = None):
    """Полная справка для администраторов"""
    roles = roles or set()
    
    if "admin" not in roles:
        await message.answer("❌ Эта команда доступна только администраторам")
        return
    
    admin_help_text = (
        "🔧 <b>Полная справка администратора КБК</b>\n\n"
        
        "🔑 <b>Управление ролями:</b>\n"
        "• /grant &lt;роль&gt; - Выдать роль (ответ на сообщение)\n"
        "• /revoke &lt;роль&gt; - Отозвать роль (ответ на сообщение)\n"
        "• /grant &lt;роль&gt; &lt;user_id&gt; - Выдать роль по ID\n"
        "• /revoke &lt;роль&gt; &lt;user_id&gt; - Отозвать роль по ID\n\n"
        
        "🔒 <b>Управление доступом:</b>\n"
        "• /lock - Переключить режим блокировки бота\n"
        "• /unlock - Принудительно выключить блокировку\n"
        "• /status - Проверить статус блокировки\n\n"
        
        "🛠 <b>Административные панели:</b>\n"
        "• /admin_panel - Главная админ панель\n"
        "• /system_stats - Системная статистика\n\n"
        
        "🧹 <b>Обслуживание системы:</b>\n"
        "• /cache_clear - Очистить кэш ролей\n\n"
        
        "📊 <b>Доступные роли:</b>\n"
        "• admin - Полный доступ ко всем функциям\n"
        "• staff - Сотрудник (управление заявками)\n"
        "• volunteer - Волонтёр (помощь участникам)\n"
        "• guest - Обычный участник (по умолчанию)\n"
        "• banned - Заблокированный пользователь\n\n"
        
        "💡 <b>Примеры использования:</b>\n"
        "• Выдать роль staff пользователю: ответьте на его сообщение и напишите /grant staff\n"
        "• Выдать роль по ID: /grant volunteer 123456789\n"
        "• Заблокировать пользователя: /grant banned 123456789\n"
        "• Включить техническое обслуживание: /lock\n"
    )
    
    await message.answer(admin_help_text)


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
            "• /admin_help - Полная справка админа\n"
            "• /admin_panel - Панель управления\n"
            "• /grant &lt;роль&gt; - Выдать роль (ответ на сообщение)\n"
            "• /revoke &lt;роль&gt; - Отозвать роль\n"
            "• /grant &lt;роль&gt; &lt;user_id&gt; - Выдать роль по ID\n"
            "• /revoke &lt;роль&gt; &lt;user_id&gt; - Отозвать роль по ID\n"
            "• /lock - Переключить режим блокировки\n"
            "• /unlock - Выключить блокировку\n"
            "• /status - Статус блокировки\n"
            "• /cache_clear - Очистить кэш ролей\n\n"
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