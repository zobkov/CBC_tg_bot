"""
Диалог главного меню для гостей
"""
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Column, Start
from aiogram.types import Message

from .states import GuestMenuSG


async def on_support_click(callback, widget, dialog_manager: DialogManager):
    """Обработчик нажатия кнопки Поддержка"""
    await dialog_manager.switch_to(GuestMenuSG.SUPPORT)


async def on_back_to_main(callback, widget, dialog_manager: DialogManager):
    """Возврат в главное меню"""
    await dialog_manager.switch_to(GuestMenuSG.MAIN)


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
        state=GuestMenuSG.SUPPORT,
    ),
)