"""
Роутер для гостей (обычные пользователи)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message

from app.bot.filters.rbac import HasRole
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="guest")

# Фильтр для гостей и всех ролей выше
router.message.filter(HasRole(Role.GUEST, Role.VOLUNTEER, Role.STAFF, Role.ADMIN))
router.callback_query.filter(HasRole(Role.GUEST, Role.VOLUNTEER, Role.STAFF, Role.ADMIN))


@router.message(F.text == "/apply")
async def apply_command(message: Message):
    """Команда для подачи заявки"""
    await message.answer(
        "📝 <b>Подача заявки на участие в КБК</b>\n\n"
        "Здесь будет запуск диалога подачи заявки.\n"
        "Пока функция в разработке.\n\n"
        "💡 В полной версии здесь будет:\n"
        "• Форма анкеты\n"
        "• Загрузка резюме\n"
        "• Выбор направления\n"
        "• Тестовые задания"
    )


@router.message(F.text == "/status")
async def status_command(message: Message, current_user=None):
    """Проверка статуса заявки"""
    if not current_user:
        await message.answer("❌ Ошибка получения данных пользователя")
        return
    
    status_map = {
        "not_submitted": "📝 Не подана",
        "submitted": "⏳ На рассмотрении",
        "approved": "✅ Одобрена",
        "rejected": "❌ Отклонена"
    }
    
    status_text = status_map.get(current_user.submission_status, "❓ Неизвестно")
    
    await message.answer(
        f"📊 <b>Статус вашей заявки</b>\n\n"
        f"Текущий статус: {status_text}\n\n"
        f"📅 Дата регистрации: {current_user.created.strftime('%d.%m.%Y %H:%M')}\n"
        f"🌐 Язык интерфейса: {current_user.language}\n\n"
        f"📌 Задания:\n"
        f"• Задание 1: {'✅ Сдано' if current_user.task_1_submitted else '📝 Не сдано'}\n"
        f"• Задание 2: {'✅ Сдано' if current_user.task_2_submitted else '📝 Не сдано'}\n"
        f"• Задание 3: {'✅ Сдано' if current_user.task_3_submitted else '📝 Не сдано'}"
    )


@router.message(F.text == "/support")
async def support_command(message: Message):
    """Команда для получения поддержки"""
    await message.answer(
        "🆘 <b>Техническая поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы:\n\n"
        "1. 📖 Ознакомьтесь с FAQ в /help\n"
        "2. 📝 Опишите вашу проблему подробно\n"
        "3. 📞 Обратитесь к волонтёрам или сотрудникам\n\n"
        "⏰ Время ответа: в рабочие дни до 24 часов\n\n"
        "📧 Также можете написать на почту: support@cbc.example.com"
    )


@router.message()
async def guest_forbidden_handler(message: Message):
    """Обработчик для недоступных гостям команд"""
    await message.answer(
        "⚠️ <b>Команда недоступна</b>\n\n"
        "Данная команда недоступна для вашего уровня доступа.\n\n"
        "Доступные команды:\n"
        "• /start - Главное меню\n"
        "• /apply - Подать заявку\n"
        "• /status - Статус заявки\n"
        "• /support - Техподдержка\n"
        "• /help - Справка"
    )