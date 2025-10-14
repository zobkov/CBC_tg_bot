"""
Диалог главного меню для сотрудников
"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Column

from .states import StaffMenuSG
from .handlers import on_support_click, on_applications_click, on_back_to_main
from .getters import get_staff_menu_data, get_applications_data, get_support_data


staff_menu_dialog = Dialog(
    Window(
        Const("👔 <b>Личный кабинет сотрудника КБК</b>\n\n"
              "Добро пожаловать в рабочий кабинет сотрудника КБК.\n\n"
              "Доступные функции:\n"
              "• Работа с заявками участников\n"
              "• Модерация контента\n"
              "• Техническая поддержка\n"
              "• Отчеты и аналитика\n\n"
              "Выберите действие:"),
        
        Column(
            Button(
                Const("📋 Анкеты"),
                id="applications",
                on_click=on_applications_click
            ),
            Button(
                Const("🆘 Поддержка"),
                id="support",
                on_click=on_support_click
            ),
        ),
        getter=get_staff_menu_data,
        state=StaffMenuSG.MAIN,
    ),
    
    Window(
        Const("📋 <b>Работа с анкетами</b>\n\n"
              "Функционал в разработке...\n\n"
              "Здесь будет:\n"
              "• Список новых заявок\n"
              "• Модерация анкет\n"
              "• Оценка заданий\n"
              "• Статистика по направлениям\n"
              "• Экспорт данных\n\n"
              "💡 Временно используйте команды:\n"
              "/applications - список заявок\n"
              "/stats - статистика"),
        
        Button(
            Const("🔙 Назад в меню"),
            id="back_main",
            on_click=on_back_to_main
        ),
        getter=get_applications_data,
        state=StaffMenuSG.APPLICATIONS,
    ),
    
    Window(
        Const("🆘 <b>Техническая поддержка</b>\n\n"
              "Раздел поддержки для сотрудников:\n\n"
              "📞 <b>Контакты команды:</b>\n"
              "• Техническая поддержка: @tech_support\n"
              "• Координаторы: @cbc_coordinators\n"
              "• Разработчики: @dev_team\n\n"
              "📋 <b>Инструкции:</b>\n"
              "• База знаний: /knowledge_base\n"
              "• Процедуры работы: /procedures\n"
              "• Отчетность: /reporting\n\n"
              "🔧 <b>Инструменты:</b>\n"
              "• Панель сотрудника: /staff_panel\n"
              "• Очередь поддержки: /support_queue"),
        
        Button(
            Const("🔙 Назад в меню"),
            id="back_main_support",
            on_click=on_back_to_main
        ),
        getter=get_support_data,
        state=StaffMenuSG.SUPPORT,
    ),
)