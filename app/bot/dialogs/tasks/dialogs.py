from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Start, Column, Cancel, SwitchTo
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import StaticMedia, DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType
from magic_filter import F

from app.bot.states.main_menu import MainMenuSG
from app.bot.states.first_stage import FirstStageSG
from app.bot.states.tasks import TasksSG

from .handlers import *
from .getters import *

task_dialog = Dialog(
    
    # Главное меню
    Window(
        Const("Диалог тестовых заданий"),
        Column(
            Button(
                Format("Тестовое задание 1"),
                id="live_task_1",
                on_click=on_live_task_1_clicked,
                when=F["task_1_is_live"]
                ),
            Button(
                Format("🔒 Тестовое задание 1"),
                id="blocked_task_1",
                when=~F["task_1_is_live"]
                ),
            Button(
                Format("Тестовое задание 2"),
                id="live_task_2",
                on_click=on_live_task_2_clicked,
                when=F["task_2_is_live"]
                ),
            Button(
                Format("🔒 Тестовое задание 2"),
                id="blocked_task_2",
                when=~F["task_2_is_live"]
                ),
            Button(
                Format("Тестовое задание 3"),
                id="live_task_3",
                on_click=on_live_task_3_clicked,
                when=F["task_3_is_live"]
                ),
            Button(
                Format("🔒 Тестовое задание 3"),
                id="blocked_task_3",
                when=~F["task_3_is_live"]
                ),
        ),
        Cancel(Const("Назад"),id="back_to_menu_from_tasks"),
        
        state=TasksSG.main,
        getter=[get_user_info, get_live_tasks_info]
    ),

    # Тестовое задание 1
    Window(
        Format("<b>Тестовое задание</b> \n{deparment_1} \nВакансия {position_1}"),

        SwitchTo(Const("Назад"),id="back_to_menu_from_task1",state=TasksSG.main),

        state=TasksSG.task_1,
        getter=get_task_1_info
    ),

    # Тестовое задание 2
    Window(
        Format("<b>Тестовое задание</b> \n{deparment_2}\nВакансия {position_2}"),

        SwitchTo(Const("Назад"),id="back_to_menu_from_task2",state=TasksSG.main),

        state=TasksSG.task_2,
        getter=get_task_2_info
    ),

    # Тестовое задание 3
    Window(
        Format("<b>Тестовое задание</b> \n{deparment_3} \nВакансия {position_3}"),

        SwitchTo(Const("Назад"),id="back_to_menu_from_task3",state=TasksSG.main),

        state=TasksSG.task_3,
        getter=get_task_3_info
    ),

)