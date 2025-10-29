"""
Роутер для сотрудников (staff)
"""
import logging
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.bot.filters.legacy_intents import create_rbac_filter_with_legacy_exclusion
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="staff")

# Фильтр для сотрудников и админов с исключением legacy интентов
staff_filter = create_rbac_filter_with_legacy_exclusion(Role.STAFF, Role.ADMIN)
router.message.filter(staff_filter)
router.callback_query.filter(staff_filter)


@router.message(Command("staff_panel"))
async def staff_panel_command(message: Message):
    """Панель управления для сотрудников"""
    await message.answer(
        "👔 <b>Панель сотрудника КБК</b>\n\n"
        "Доступные функции:\n\n"
        "📊 <b>Аналитика:</b>\n"
        "• /applications - Список заявок\n"
        "• /stats - Подробная статистика\n"
        "• /export - Экспорт данных\n\n"
        "⚙️ <b>Управление:</b>\n"
        "• /broadcast - Рассылка уведомлений\n"
        "• /moderate - Модерация контента\n"
        "• /support_queue - Очередь поддержки\n\n"
        "👥 <b>Пользователи:</b>\n"
        "• /user_info <id> - Информация о пользователе\n"
        "• /user_status <id> - Изменить статус заявки"
    )


@router.message(Command("applications"))
async def applications_command(message: Message, db=None):
    """Список заявок для модерации"""
    if not db:
        await message.answer("❌ Ошибка доступа к базе данных")
        return
    
    try:
        # TODO: Реализовать получение списка заявок
        await message.answer(
            "📋 <b>Список заявок</b>\n\n"
            "В разработке...\n\n"
            "Будет показывать:\n"
            "• Новые заявки на рассмотрении\n"
            "• Статистику по направлениям\n"
            "• Задания на проверку\n"
            "• Фильтры по статусу"
        )
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        await message.answer("❌ Ошибка при получении заявок")


@router.message(Command("stats"))
async def detailed_stats_command(message: Message, db=None):
    """Подробная статистика для сотрудников"""
    if not db:
        await message.answer("❌ Ошибка доступа к базе данных")
        return
    
    try:
        # TODO: Реализовать подробную статистику
        await message.answer(
            "📈 <b>Подробная статистика</b>\n\n"
            "В разработке...\n\n"
            "Будет включать:\n"
            "• Динамику подач заявок\n"
            "• Конверсию по этапам\n"
            "• Активность пользователей\n"
            "• Нагрузку на поддержку\n"
            "• Географическое распределение"
        )
    except Exception as e:
        logger.error(f"Error getting detailed stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.message(Command("user_info"))
async def user_info_command(message: Message, command: CommandObject, db=None):
    """Информация о конкретном пользователе"""
    try:
        # Используем аргументы команды
        if not command.args:
            await message.answer(
                "❌ Укажите ID пользователя\n"
                "Пример: /user_info 123456789"
            )
            return
        
        user_id = int(command.args.strip())
        
        if not db:
            await message.answer("❌ Ошибка доступа к базе данных")
            return
        
        user = await db.users.get_user_record(user_id=user_id)
        if not user:
            await message.answer(f"❌ Пользователь {user_id} не найден")
            return
        
        roles_text = ", ".join(user.roles) if user.roles else "нет ролей"
        
        info_text = (
            f"👤 <b>Информация о пользователе {user_id}</b>\n\n"
            f"📅 Регистрация: {user.created.strftime('%d.%m.%Y %H:%M')}\n"
            f"🌐 Язык: {user.language}\n"
            f"🏷 Роли: {roles_text}\n"
            f"💚 Активен: {'Да' if user.is_alive else 'Нет'}\n"
            f"🚫 Заблокирован: {'Да' if user.is_blocked else 'Нет'}\n"
            f"📊 Статус заявки: {user.submission_status}\n\n"
            f"📌 <b>Задания:</b>\n"
            f"• Задание 1: {'✅ Сдано' if user.task_1_submitted else '📝 Не сдано'}\n"
            f"• Задание 2: {'✅ Сдано' if user.task_2_submitted else '📝 Не сдано'}\n"
            f"• Задание 3: {'✅ Сдано' if user.task_3_submitted else '📝 Не сдано'}"
        )
        
        await message.answer(info_text)
        
    except ValueError:
        await message.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        await message.answer("❌ Ошибка при получении информации о пользователе")


@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """Команда для массовой рассылки"""
    await message.answer(
        "📢 <b>Система рассылок</b>\n\n"
        "В разработке...\n\n"
        "Будет позволять:\n"
        "• Отправлять уведомления группам пользователей\n"
        "• Планировать рассылки\n"
        "• Отслеживать статус доставки\n"
        "• Использовать шаблоны сообщений\n\n"
        "💡 Пока используйте существующий функционал рассылок"
    )


@router.message(Command("support_queue"))
async def support_queue_command(message: Message):
    """Очередь обращений в поддержку"""
    await message.answer(
        "🎫 <b>Очередь поддержки</b>\n\n"
        "В разработке...\n\n"
        "Будет показывать:\n"
        "• Новые обращения\n"
        "• Обращения в работе\n"
        "• Эскалированные вопросы\n"
        "• Статистику по времени ответа"
    )