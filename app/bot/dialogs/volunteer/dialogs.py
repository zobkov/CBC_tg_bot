"""
Диалог главного меню для волонтёров
"""
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Column, Start
from aiogram.types import Message

from .states import VolunteerMenuSG


async def on_support_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Поддержка"""
    await dialog_manager.switch_to(VolunteerMenuSG.SUPPORT)


async def on_help_users_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Помощь пользователям"""
    await dialog_manager.switch_to(VolunteerMenuSG.HELP_USERS)


async def on_back_to_main(callback, widget, dialog_manager: DialogManager):
    """Возврат в главное меню"""
    await dialog_manager.switch_to(VolunteerMenuSG.MAIN)


volunteer_menu_dialog = Dialog(
    Window(
        Const("🤝 <b>Личный кабинет волонтёра КБК</b>\n\n"
              "Добро пожаловать в кабинет волонтёра КБК.\n\n"
              "Ваши функции:\n"
              "• Помощь новым участникам\n"
              "• Ответы на частые вопросы\n"
              "• Информационная поддержка\n"
              "• Направление к специалистам\n\n"
              "Выберите действие:"),
        
        Column(
            Button(
                Const("👥 Помощь пользователям"),
                id="help_users",
                on_click=on_help_users_click
            ),
            Button(
                Const("🆘 Поддержка"),
                id="support",
                on_click=on_support_click
            ),
        ),
        state=VolunteerMenuSG.MAIN,
    ),
    
    Window(
        Const("👥 <b>Помощь пользователям</b>\n\n"
              "Инструменты для помощи участникам:\n\n"
              "📋 <b>База знаний:</b>\n"
              "• Частые вопросы: /faq\n"
              "• Инструкции: /instructions\n"
              "• Контакты: /contacts\n\n"
              "📊 <b>Статистика:</b>\n"
              "• Активные пользователи: /volunteer_stats\n"
              "• Обращения: /support_stats\n\n"
              "🔄 <b>Эскалация:</b>\n"
              "• Передать сотрудникам: /escalate\n"
              "• Срочные вопросы: /urgent\n\n"
              "💡 Всегда будьте вежливы и терпеливы!"),
        
        Button(
            Const("🔙 Назад в меню"),
            id="back_main",
            on_click=on_back_to_main
        ),
        state=VolunteerMenuSG.HELP_USERS,
    ),
    
    Window(
        Const("🆘 <b>Поддержка волонтёров</b>\n\n"
              "Раздел поддержки для волонтёров:\n\n"
              "📞 <b>Контакты:</b>\n"
              "• Координатор волонтёров: @volunteer_lead\n"
              "• Сотрудники КБК: @cbc_staff\n"
              "• Техподдержка: @tech_support\n\n"
              "📚 <b>Обучение:</b>\n"
              "• Справочник волонтёра: /volunteer_guide\n"
              "• Обучающие материалы: /training\n"
              "• Вебинары: /webinars\n\n"
              "🎯 <b>Ваши инструменты:</b>\n"
              "• Справка для волонтёров: /volunteer_help\n"
              "• База знаний: /faq"),
        
        Button(
            Const("🔙 Назад в меню"),
            id="back_main_support",
            on_click=on_back_to_main
        ),
        state=VolunteerMenuSG.SUPPORT,
    ),
)