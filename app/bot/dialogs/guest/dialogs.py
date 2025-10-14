"""
Диалог главного меню для гостей
"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Column

from .states import GuestMenuSG
from .handlers import on_support_click, on_back_to_main
from .getters import get_guest_menu_data, get_support_data


guest_menu_dialog = Dialog(
    Window(
        Const("🎯 <b>Личный кабинет участника КБК</b>\n\n"
              "Добро пожаловать в систему отбора команды КБК!\n\n"
              "Здесь вы можете:\n"
              "• Подать заявку на участие\n"
              "• Отслеживать статус заявки\n"
              "• Выполнять задания\n"
              "• Получать поддержку\n\n"
              "Выберите действие:"),
        
        Column(
            Button(
                Const("🆘 Поддержка"),
                id="support",
                on_click=on_support_click
            ),
            # TODO: Добавить кнопки для заявки, статуса и заданий
            # когда legacy диалоги будут адаптированы под роли
        ),
        getter=get_guest_menu_data,
        state=GuestMenuSG.MAIN,
    ),
    
    Window(
        Const("🆘 <b>Техническая поддержка</b>\n\n"
              "Если у вас возникли вопросы или проблемы:\n\n"
              "1. 📖 Ознакомьтесь с FAQ в справке\n"
              "2. 📝 Опишите вашу проблему подробно\n"
              "3. 📞 Обратитесь к волонтёрам или сотрудникам\n\n"
              "⏰ Время ответа: в рабочие дни до 24 часов\n\n"
              "📧 Также можете написать на почту:\n"
              "support@cbc.example.com"),
        
        Button(
            Const("🔙 Назад в меню"),
            id="back_main",
            on_click=on_back_to_main
        ),
        getter=get_support_data,
        state=GuestMenuSG.SUPPORT,
    ),
)