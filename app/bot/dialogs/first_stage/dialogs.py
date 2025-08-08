from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Radio, Column, Next, Back, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram.enums import ContentType

from app.bot.states.first_stage import FirstStageSG
from .getters import (
    get_stage_info, get_how_found_options, get_departments, 
    get_positions_for_department, get_course_options, get_form_summary
)
from .handlers import (
    on_apply_clicked, on_full_name_input, on_university_input,
    on_phone_input, on_email_input, on_course_selected, 
    on_how_found_selected, on_department_selected, on_position_selected,
    on_experience_input, on_motivation_input, on_resume_uploaded,
    on_confirm_application
)

first_stage_dialog = Dialog(
    # Информация о первом этапе
    Window(
        Format("📋 <b>{stage_name}</b>\n\n{stage_description}\n\n"
               "{application_status_text}"),
        Button(
            Const("📝 Подать заявку"),
            id="apply",
            on_click=on_apply_clicked,
            when="can_apply"
        ),
        Cancel(Const("◀️ Назад в меню")),
        state=FirstStageSG.stage_info,
        getter=get_stage_info
    ),
    
    # ФИО
    Window(
        Const("👤 <b>Введите ваше ФИО</b>\n\nПример: Иванов Иван Иванович"),
        MessageInput(
            func=on_full_name_input,
            content_types=[ContentType.TEXT]
        ),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.full_name
    ),
    
    # Учебное заведение
    Window(
        Const("🏫 <b>Введите ваше учебное заведение</b>\n\nПример: СПбГУ"),
        MessageInput(
            func=on_university_input,
            content_types=[ContentType.TEXT]
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.university
    ),
    
    # Курс
    Window(
        Const("📚 <b>Выберите ваш курс</b>"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="course_radio",
                item_id_getter=lambda item: item["id"],
                items="courses",
                on_click=on_course_selected
            ),
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.course,
        getter=get_course_options
    ),
    
    # Телефон
    Window(
        Const("📱 <b>Введите ваш номер телефона</b>\n\nПример: +7 (012) 345-67-89"),
        MessageInput(
            func=on_phone_input,
            content_types=[ContentType.TEXT]
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.phone
    ),
    
    # Email
    Window(
        Const("📧 <b>Введите ваш email</b>\n\nПример: example@mail.com"),
        MessageInput(
            func=on_email_input,
            content_types=[ContentType.TEXT]
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.email
    ),
    
    # Откуда узнали о КБК
    Window(
        Const("📢 <b>Откуда вы узнали о КБК?</b>"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="how_found_radio",
                item_id_getter=lambda item: item["id"],
                items="how_found_options",
                on_click=on_how_found_selected
            ),
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.how_found_kbk,
        getter=get_how_found_options
    ),
    
    # Выбор отдела
    Window(
        Const("🏢 <b>Выберите отдел</b>"),
        Column(
            Radio(
                Format("🔘 {item[text]}\n📝 {item[description]}"),
                Format("⚪ {item[text]}\n📝 {item[description]}"),
                id="department_radio",
                item_id_getter=lambda item: item["id"],
                items="departments",
                on_click=on_department_selected
            ),
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.department,
        getter=get_departments
    ),
    
    # Выбор должности
    Window(
        Format("💼 <b>Выберите должность в отделе: {department_name}</b>"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="position_radio",
                item_id_getter=lambda item: item["id"],
                items="positions",
                on_click=on_position_selected
            ),
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.position,
        getter=get_positions_for_department
    ),
    
    # Опыт
    Window(
        Const("💼 <b>Расскажите о своем опыте</b>\n\n"
              "Опишите проекты, в которых участвовали, выполняемые задачи и достигнутые результаты.\n"
              "Если серьезного опыта пока нет — опишите ситуации, где проявляли инициативу и ответственность."),
        MessageInput(
            func=on_experience_input,
            content_types=[ContentType.TEXT]
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.experience
    ),
    
    # Мотивация
    Window(
        Const("💭 <b>Расскажите о своей мотивации</b>\n\n"
              "Кратко объясните, почему хотите присоединиться к команде КБК "
              "и что ожидаете от работы в оргкомитете."),
        MessageInput(
            func=on_motivation_input,
            content_types=[ContentType.TEXT]
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.motivation
    ),
    
    # Загрузка резюме
    Window(
        Const("📎 <b>Загрузите ваше резюме</b>\n\n"
              "Отправьте файл с резюме (PDF, DOC, DOCX)"),
        MessageInput(
            func=on_resume_uploaded,
            content_types=[ContentType.DOCUMENT]
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.resume_upload
    ),
    
    # Подтверждение
    Window(
        Format("✅ <b>Проверьте данные заявки</b>\n\n"
               "👤 <b>ФИО:</b> {full_name}\n"
               "🏫 <b>Учебное заведение:</b> {university}\n"
               "📚 <b>Курс:</b> {course_text}\n"
               "📱 <b>Телефон:</b> {phone}\n"
               "📧 <b>Email:</b> {email}\n"
               "📢 <b>Откуда узнали:</b> {how_found_text}\n"
               "🏢 <b>Отдел:</b> {department_name}\n"
               "💼 <b>Должность:</b> {position_text}\n"
               "💼 <b>Опыт:</b> {experience}\n"
               "💭 <b>Мотивация:</b> {motivation}\n"
               "📎 <b>Резюме:</b> {resume_status}"),
        Button(
            Const("✅ Подтвердить и отправить"),
            id="confirm",
            on_click=on_confirm_application
        ),
        Back(Const("◀️ Назад")),
        Cancel(Const("❌ Отменить")),
        state=FirstStageSG.confirmation,
        getter=get_form_summary
    ),
    
    # Успешная отправка
    Window(
        Const("🎉 <b>Заявка успешно отправлена!</b>\n\n"
              "Спасибо за интерес к КБК! Мы рассмотрим вашу заявку и свяжемся с вами в ближайшее время.\n\n"
              "Следите за обновлениями в нашем телеграм-канале!"),
        Cancel(Const("🏠 В главное меню")),
        state=FirstStageSG.success
    ),
)
