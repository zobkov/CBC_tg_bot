from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Start, Column, Cancel, SwitchTo
from aiogram_dialog.widgets.input import MessageInput
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
        Format("📝 <b>Тестовые задания</b> \n\nНиже представлен список вакансий, которые ты выбрал в качестве приоритетных. Ты можешь открыть тестовые задания для каждой позиции и выбрать ту, что ближе тебе по духу." \
        "\n\n<b>Приоритет №1:</b> <i>{task_1_header}</i>" \
        "\n<b>Приоритет №2:</b> <i>{task_2_header}</i>" \
        "\n<b>Приоритет №3:</b> <i>{task_3_header}</i>" \
        "\n\n⚠️ Если рядом с вакансией отображается «замочек», это значит, что этот приоритет не был одобрен для прохождения. Сосредоточься на направлениях, где доступ открыт. Мы уверены, у тебя все получится!"),
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
        getter=[get_user_info, get_live_tasks_info, get_task_1_info, get_task_2_info, get_task_3_info]
    ),

    # Тестовое задание 1
    Window(
        Format("📝<b>Тестовое задание</b> \n{task_1_header}" \
        "\n\nВ этом меню ты найдёшь тестовое задание по выбранной вакансии. Файл прикреплён выше в формате PDF. Здесь же ты можешь загрузить своё решение: прикрепи один или несколько файлов в разных форматах. Если загрузил не те документы — всегда можно удалить их и прикрепить заново. Будь внимателен: после того как отправишь решение на проверку, изменить его уже нельзя." \
        "\n\n⏰ <b>Дедлайн:</b> до 2 октября 2025 года, 23:59 (МСК)" \
        "\n\nЕсли возникнут технические вопросы, наша поддержка всегда рядом и готова помочь – @zobko"),
        DynamicMedia("task_1"),
        SwitchTo(Const("📥 Загрузка решения"),id="task_1_to_upload_1",state=TasksSG.task_1_upload),
        SwitchTo(Const("Назад"),id="back_to_menu_from_task1",state=TasksSG.main),

        state=TasksSG.task_1,
        getter=[get_task_1_info, get_tasks_files]
    ),

    # Тестовое задание 2
    Window(
        Format("📝<b>Тестовое задание</b> \n{task_2_header}" \
        "\n\nВ этом меню ты найдёшь тестовое задание по выбранной вакансии. Файл прикреплён выше в формате PDF. Здесь же ты можешь загрузить своё решение: прикрепи один или несколько файлов в разных форматах. Если загрузил не те документы — всегда можно удалить их и прикрепить заново. Будь внимателен: после того как отправишь решение на проверку, изменить его уже нельзя." \
        "\n\n⏰ <b>Дедлайн:</b> до 2 октября 2025 года, 23:59 (МСК)" \
        "\n\nЕсли возникнут технические вопросы, наша поддержка всегда рядом и готова помочь – @zobko"),
        DynamicMedia("task_2"),
        SwitchTo(Const("📥 Загрузка решения"),id="task_2_to_upload_2",state=TasksSG.task_2_upload),
        SwitchTo(Const("Назад"),id="back_to_menu_from_task2",state=TasksSG.main),

        state=TasksSG.task_2,
        getter=[get_task_2_info, get_tasks_files]
    ),

    # Тестовое задание 3
    Window(
        Format("📝<b>Тестовое задание</b> \n{task_3_header}" \
        "\n\nВ этом меню ты найдёшь тестовое задание по выбранной вакансии. Файл прикреплён выше в формате PDF. Здесь же ты можешь загрузить своё решение: прикрепи один или несколько файлов в разных форматах. Если загрузил не те документы — всегда можно удалить их и прикрепить заново. Будь внимателен: после того как отправишь решение на проверку, изменить его уже нельзя." \
        "\n\n⏰ <b>Дедлайн:</b> до 2 октября 2025 года, 23:59 (МСК)" \
        "\n\nЕсли возникнут технические вопросы, наша поддержка всегда рядом и готова помочь – @zobko"),
        DynamicMedia("task_3"),
        SwitchTo(Const("📥 Загрузка решения"),id="task_3_to_upload_3",state=TasksSG.task_3_upload),
        SwitchTo(Const("Назад"),id="back_to_menu_from_task3",state=TasksSG.main),

        state=TasksSG.task_3,
        getter=[get_task_3_info, get_tasks_files]
    ),

    # Загрузка тестового 1
    Window(
        Format("📝 <b>Загрузка решения для задания 1</b>\n\n"
               "Для загрузки просто отправляй файлы сюда. Когда закончишь отправлять файлы, нажми на кнопку завершения отправки.\n\n"
               "<b>ВНИМАНИЕ! После завершения отправки невозможно будет поменять или отправить еще файлы!</b>\n"
               "Если ты думаешь, что произошла техническая ошибка – Пиши @zobko\n\n"
               "<b>Загруженные файлы:</b>\n{files_text}"),
        Column(
            Button(
                Const("❌ Удалить ВСЕ файлы"), 
                id="delete_all_files_task_1",
                on_click=on_delete_all_files_task_1
            ),
            Button(
                Const("✅ Закончить отправку и завершить задание"), 
                id="confirm_upload_task_1", 
                on_click=on_confirm_upload_task_1
            ),
            SwitchTo(Const("⬅️ Назад"), id="back_from_upload_1", state=TasksSG.task_1),
        ),
        MessageInput(
            on_document_upload_task_1, 
            content_types=[ContentType.DOCUMENT]
        ),
        MessageInput(
            on_wrong_content_type,
            content_types=[ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO, ContentType.AUDIO, ContentType.VOICE, ContentType.STICKER, ContentType.ANIMATION, ContentType.VIDEO_NOTE, ContentType.LOCATION, ContentType.CONTACT]
        ),

        state=TasksSG.task_1_upload,
        getter=[get_task_1_info, get_user_files_info_task_1]
    ),

    # Загрузка тестового 2
    Window(
        Format("📝 <b>Загрузка решения для задания 2</b>\n\n"
               "Для загрузки просто отправляй файлы сюда. Когда закончишь отправлять файлы, нажми на кнопку завершения отправки.\n\n"
               "<b>ВНИМАНИЕ! После завершения отправки невозможно будет поменять или отправить еще файлы!</b>\n"
               "Если ты думаешь, что произошла техническая ошибка – Пиши @zobko\n\n"
               "<b>Загруженные файлы:</b>\n{files_text}"),
        Column(
            Button(
                Const("❌ Удалить ВСЕ файлы"), 
                id="delete_all_files_task_2",
                on_click=on_delete_all_files_task_2
            ),
            Button(
                Const("✅ Закончить отправку и завершить задание"), 
                id="confirm_upload_task_2", 
                on_click=on_confirm_upload_task_2
            ),
            SwitchTo(Const("⬅️ Назад"), id="back_from_upload_2", state=TasksSG.task_2),
        ),
        MessageInput(
            on_document_upload_task_2, 
            content_types=[ContentType.DOCUMENT]
        ),
        MessageInput(
            on_wrong_content_type,
            content_types=[ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO, ContentType.AUDIO, ContentType.VOICE, ContentType.STICKER, ContentType.ANIMATION, ContentType.VIDEO_NOTE, ContentType.LOCATION, ContentType.CONTACT]
        ),

        state=TasksSG.task_2_upload,
        getter=[get_task_2_info, get_user_files_info_task_2]
    ),

    # Загрузка тестового 3
    Window(
        Format("📝 <b>Загрузка решения для задания 3</b>\n\n"
               "Для загрузки просто отправляй файлы сюда. Когда закончишь отправлять файлы, нажми на кнопку завершения отправки.\n\n"
               "<b>ВНИМАНИЕ! После завершения отправки невозможно будет поменять или отправить еще файлы!</b>\n"
               "Если ты думаешь, что произошла техническая ошибка – Пиши @zobko\n\n"
               "<b>Загруженные файлы:</b>\n{files_text}"),
        Column(
            Button(
                Const("❌ Удалить ВСЕ файлы"), 
                id="delete_all_files_task_3",
                on_click=on_delete_all_files_task_3
            ),
            Button(
                Const("✅ Закончить отправку и завершить задание"), 
                id="confirm_upload_task_3", 
                on_click=on_confirm_upload_task_3
            ),
            SwitchTo(Const("⬅️ Назад"), id="back_from_upload_3", state=TasksSG.task_3),
        ),
        MessageInput(
            on_document_upload_task_3, 
            content_types=[ContentType.DOCUMENT]
        ),
        MessageInput(
            on_wrong_content_type,
            content_types=[ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO, ContentType.AUDIO, ContentType.VOICE, ContentType.STICKER, ContentType.ANIMATION, ContentType.VIDEO_NOTE, ContentType.LOCATION, ContentType.CONTACT]
        ),

        state=TasksSG.task_3_upload,
        getter=[get_task_3_info, get_user_files_info_task_3]
    ),

    # Уже отправлено задание 1
    Window(
        Format("🚀 <b>Решение отправлено! </b>\n\n"
               "Нам уже не терпится начать проверку, чтобы лучше познакомиться с тобой и понять, как ты смотришь на мир.\n"
               "📅 Результаты будут объявлены 7 октября в 12:00 (МСК)."),
        SwitchTo(Const("⬅️ Назад"), id="back_from_submitted_1", state=TasksSG.main),
        state=TasksSG.task_1_submitted
    ),

    # Уже отправлено задание 2
    Window(
        Format("🚀 <b>Решение отправлено! </b>\n\n"
               "Нам уже не терпится начать проверку, чтобы лучше познакомиться с тобой и понять, как ты смотришь на мир.\n"
               "📅 Результаты будут объявлены 7 октября в 12:00 (МСК)."),
        SwitchTo(Const("⬅️ Назад"), id="back_from_submitted_2", state=TasksSG.main),
        state=TasksSG.task_2_submitted
    ),

    # Уже отправлено задание 3
    Window(
        Format("🚀 <b>Решение отправлено! </b>\n\n"
               "Нам уже не терпится начать проверку, чтобы лучше познакомиться с тобой и понять, как ты смотришь на мир.\n"
               "📅 Результаты будут объявлены 7 октября в 12:00 (МСК)."),
        SwitchTo(Const("⬅️ Назад"), id="back_from_submitted_3", state=TasksSG.main),
        state=TasksSG.task_3_submitted
    ),

    # Обработка файлов для задания 1
    Window(
        Const("⏳ <b>Обработка файлов...</b>\n\n"
              "Пожалуйста, подождите. Ваши файлы обрабатываются.\n"
              "Когда все файлы будут обработаны, нажмите кнопку ниже чтобы продолжить."),
        SwitchTo(Const("📥 Продолжить загрузку"), id="back_to_upload_1", state=TasksSG.task_1_upload),
        state=TasksSG.task_1_processing
    ),

    # Обработка файлов для задания 2
    Window(
        Const("⏳ <b>Обработка файлов...</b>\n\n"
              "Пожалуйста, подождите. Ваши файлы обрабатываются.\n"
              "Когда все файлы будут обработаны, нажмите кнопку ниже чтобы продолжить."),
        SwitchTo(Const("📥 Продолжить загрузку"), id="back_to_upload_2", state=TasksSG.task_2_upload),
        state=TasksSG.task_2_processing
    ),

    # Обработка файлов для задания 3
    Window(
        Const("⏳ <b>Обработка файлов...</b>\n\n"
              "Пожалуйста, подождите. Ваши файлы обрабатываются.\n"
              "Когда все файлы будут обработаны, нажмите кнопку ниже чтобы продолжить."),
        SwitchTo(Const("📥 Продолжить загрузку"), id="back_to_upload_3", state=TasksSG.task_3_upload),
        state=TasksSG.task_3_processing
    ),

    Window(
        Const("⚙️ Файлы обрабатываются..."),
        state=TasksSG.file_processing,
    )

)