"""
Роутер для волонтёров
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters.rbac import HasRole
from app.bot.filters.legacy_intents import create_rbac_filter_with_legacy_exclusion
from app.enums.roles import Role

logger = logging.getLogger(__name__)

router = Router(name="volunteer")

# Фильтр для волонтёров и ролей выше с исключением legacy интентов
volunteer_filter = create_rbac_filter_with_legacy_exclusion(Role.VOLUNTEER, Role.STAFF, Role.ADMIN)
router.message.filter(volunteer_filter)
router.callback_query.filter(volunteer_filter)


@router.message(Command("volunteer_help"))
async def volunteer_help_command(message: Message):
    """Справка для волонтёров"""
    await message.answer(
        "🤝 <b>Справка для волонтёров КБК</b>\n\n"
        "Ваши основные задачи:\n"
        "• Помощь новым участникам\n"
        "• Ответы на частые вопросы\n"
        "• Направление к специалистам при необходимости\n\n"
        "Доступные команды:\n"
        "• /volunteer_stats - Статистика участников\n"
        "• /faq - База знаний для участников\n"
        "• /escalate - Передать вопрос сотрудникам\n\n"
        "📋 Помните: всегда будьте вежливы и терпеливы!"
    )


@router.message(Command("volunteer_stats"))
async def volunteer_stats_command(message: Message, db=None):
    """Базовая статистика для волонтёров"""
    if not db:
        await message.answer("❌ Ошибка доступа к базе данных")
        return
    
    try:
        # Получаем базовую статистику
        # TODO: Добавить методы в БД для получения статистики
        await message.answer(
            "📊 <b>Статистика участников</b>\n\n"
            "В разработке...\n\n"
            "Будет показывать:\n"
            "• Общее количество участников\n"
            "• Количество поданных заявок\n"
            "• Активные пользователи за день\n"
            "• Частые вопросы"
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.message(Command("faq"))
async def faq_command(message: Message):
    """База знаний для помощи участникам"""
    await message.answer(
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "<b>1. Как подать заявку?</b>\n"
        "Используйте команду /apply и следуйте инструкциям.\n\n"
        "<b>2. Когда будут результаты?</b>\n"
        "Результаты объявляются поэтапно, следите за уведомлениями.\n\n"
        "<b>3. Можно ли изменить заявку?</b>\n"
        "До дедлайна заявку можно редактировать.\n\n"
        "<b>4. Что делать, если бот не отвечает?</b>\n"
        "Попробуйте /start или обратитесь в поддержку.\n\n"
        "<b>5. Как связаться с организаторами?</b>\n"
        "Используйте /support для связи с командой."
    )


@router.message(Command("escalate"))
async def escalate_command(message: Message):
    """Передача вопроса сотрудникам"""
    await message.answer(
        "🔄 <b>Передача вопроса сотрудникам</b>\n\n"
        "Если вопрос участника требует вмешательства сотрудников,\n"
        "переадресуйте его к команде поддержки.\n\n"
        "📝 Укажите:\n"
        "• ID пользователя\n"
        "• Суть проблемы\n"
        "• Что уже было предпринято\n\n"
        "⚡ Сотрудники будут уведомлены о новом обращении."
    )