from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager

from app.bot.states.first_stage import FirstStageSG
from app.bot.states.main_menu import MainMenuSG
from app.bot.states.tasks import TasksSG
from app.infrastructure.database.database.db import DB


async def on_current_stage_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Тестовые задания'"""
    # Сначала отвечаем на callback, чтобы избежать таймаута
    await callback.answer()
    
    # Получаем доступ к базе данных
    db: DB = dialog_manager.middleware_data.get("db")
    event_from_user = dialog_manager.event.from_user
    
    # Проверяем, прошел ли пользователь первый этап
    if db:
        try:
            evaluation = await db.evaluated_applications.get_evaluation(user_id=event_from_user.id)
            
            if evaluation:
                # Если все accepted_1, accepted_2, accepted_3 = False, значит не прошел
                is_first_stage_passed = evaluation.accepted_1 or evaluation.accepted_2 or evaluation.accepted_3
                
                if not is_first_stage_passed:
                    # Отправляем сообщение о недоступности и не переходим никуда
                    await callback.message.answer("""Мы внимательно изучили более 300 заявок. Конкуренция была очень высокой, и к сожалению, на этот раз твой путь в рамках основного отбора на этом завершается. Это не приговор, это – точка роста, от которой можно (и нужно!) двигаться дальше. Мы будем рады видеть тебя на других активностях КБК'26.

Мы верим в твой потенциал и хотим, чтобы ты продолжал раскрывать себя. В следующих заявках попробуй подробнее делиться тем, что для тебя действительно важно: опытом, мыслями, идеями, тем, что тебя вдохновляет. Позволь нам увидеть за строчками анкеты живого человека: твой характер, ценности и амбиции.
Уверены, впереди ещё много пересечений и возможностей, где твоя уникальность сможет проявиться в полной мере.

Никогда не останавливайся и смело двигайся вперёд, и мы уверены, что наши пути ещё обязательно пересекутся!""")
                    return
            else:
                # Если пользователя нет в evaluated_applications, значит он не отправлял заявку
                await callback.message.answer("""Мы внимательно изучили более 300 заявок. Конкуренция была очень высокой, и к сожалению, на этот раз твой путь в рамках основного отбора на этом завершается. Это не приговор, это – точка роста, от которой можно (и нужно!) двигаться дальше. Мы будем рады видеть тебя на других активностях КБК'26.

Мы верим в твой потенциал и хотим, чтобы ты продолжал раскрывать себя. В следующих заявках попробуй подробнее делиться тем, что для тебя действительно важно: опытом, мыслями, идеями, тем, что тебя вдохновляет. Позволь нам увидеть за строчками анкеты живого человека: твой характер, ценности и амбиции.
Уверены, впереди ещё много пересечений и возможностей, где твоя уникальность сможет проявиться в полной мере.

Никогда не останавливайся и смело двигайся вперёд, и мы уверены, что наши пути ещё обязательно пересекутся!""")
                return
        except Exception:
            # В случае ошибки разрешаем доступ
            pass
    
    # Переходим к диалогу с тестовыми заданиями
    await dialog_manager.start(state=TasksSG.main)


async def on_support_clicked(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Обработчик нажатия на кнопку 'Поддержка'"""
    # Переходим к окну поддержки
    await dialog_manager.switch_to(state=MainMenuSG.support)
