from aiogram_dialog.widgets.kbd import Button, Radio, Column, Next, Back, Multiselect, Row
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram.enums import ContentType

from app.bot.states.first_stage import FirstStageSG
from .getters import (
    get_stage_info, get_how_found_options, get_departments, get_departments_for_previous,
    get_positions_for_department, get_course_options, get_form_summary,
    get_edit_menu_data, get_edit_how_found_options
)
from .handlers import (
    on_apply_clicked, on_full_name_input, on_university_input,
    on_phone_input, on_email_input, on_course_selected, 
    on_how_found_state_changed, on_how_found_continue, on_previous_department_selected,
    on_department_selected, on_position_selected,
    on_experience_input, on_motivation_input, on_resume_uploaded,
    on_confirm_application, on_edit_clicked, on_edit_field_clicked, on_back_to_confirmation,
    on_edit_full_name_input, on_edit_university_input, on_edit_course_selected,
    on_edit_phone_input, on_edit_email_input, on_edit_how_found_state_changed,
    on_edit_how_found_continue, on_edit_previous_department_selected,
    on_edit_experience_input, on_edit_motivation_input, on_edit_resume_uploaded,
    on_edit_department_selected, on_edit_position_selected
)
from .getters import (
    get_stage_info, get_how_found_options, get_departments, get_departments_for_previous,
    get_positions_for_department, get_course_options, get_form_summary
)
from .handlers import (
    on_apply_clicked, on_full_name_input, on_university_input,
    on_phone_input, on_email_input, on_course_selected, 
    on_how_found_state_changed, on_how_found_continue, on_previous_department_selected,
    on_department_selected, on_position_selected,
    on_experience_input, on_motivation_input, on_resume_uploaded,
    on_confirm_application, on_edit_clicked, on_edit_field_clicked, on_back_to_confirmation,
    on_edit_full_name_input, on_edit_university_input, on_edit_course_selected,
    on_edit_phone_input, on_edit_email_input, on_edit_how_found_state_changed,
    on_edit_experience_input, on_edit_motivation_input, on_edit_resume_uploaded,
    on_experience_input, on_motivation_input, on_resume_uploaded,
    on_confirm_application, go_to_menu, on_job_selection_result
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
        Button(Const("🏠 В главное меню"), id="go_to_menu", on_click=go_to_menu),
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
        state=FirstStageSG.full_name
    ),
    
    # Учебное заведение
    Window(
        Const("🏫 <b>Введите ваше место учебы: название учебного заведения, факультет, курс и год выпуска</b>\n\nПример: СПбГУ, ВШМ, 2 курс, 2027"),
        MessageInput(
            func=on_university_input,
            content_types=[ContentType.TEXT]
        ),
        state=FirstStageSG.university
    ),

    # Телефон
    Window(
        Const("📱 <b>Введите ваш номер телефона</b>\n\nПример: +7 (012) 345-67-89"),
        MessageInput(
            func=on_phone_input,
            content_types=[ContentType.TEXT]
        ),
        state=FirstStageSG.phone
    ),
    
    # Email
    Window(
        Const("📧 <b>Введите ваш email</b>\n\nПример: example@mail.com"),
        MessageInput(
            func=on_email_input,
            content_types=[ContentType.TEXT]
        ),
        state=FirstStageSG.email
    ),
    
    # Откуда узнали о КБК (множественный выбор)
    Window(
        Const("📢 <b>Откуда вы узнали о КБК?</b>\n\n<i>Можно выбрать несколько вариантов</i>"),
        Column(
            Multiselect(
                Format("✅ {item[text]}"),  # checked_text
                Format("☐ {item[text]}"),   # unchecked_text
                id="how_found_multiselect",
                item_id_getter=lambda item: item["id"],
                items="how_found_options",
                min_selected=1,
                on_state_changed=on_how_found_state_changed
            ),
        ),
        Button(
            Const("➡️ Далее"),
            id="continue_how_found",
            on_click=on_how_found_continue, # TODO тут переход в выбор ваканссии
            when="has_selections"
        ),
        state=FirstStageSG.how_found_kbk,
        getter=get_how_found_options
    ),
    
    # Отдел предыдущего участия (если выбрано "Ранее участвовал в КБК")
    Window(
        Const("🏢 <b>В каком отделе вы участвовали в КБК ранее?</b>"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="previous_dept_radio",
                item_id_getter=lambda item: item["id"],
                items="departments",
                on_click=on_previous_department_selected # TODO тут переход в выбор ваканссии
            ),
        ),
        state=FirstStageSG.previous_department,
        getter=get_departments_for_previous
    ),
    

    # Выбор отдела


    # Опыт
    Window(
        Const("💼 <b>Расскажите о своем опыте</b>\n\n"
              "Опишите проекты, в которых участвовали, выполняемые задачи и достигнутые результаты.\n"
              "Если серьезного опыта пока нет — опишите ситуации, где проявляли инициативу и ответственность."),
        MessageInput(
            func=on_experience_input,
            content_types=[ContentType.TEXT]
        ),
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
        state=FirstStageSG.motivation
    ),
    
    # Загрузка резюме
    Window(
        Const("📎 <b>Загрузите ваше резюме</b>\n\n"
              "Отправьте файл с резюме (PDF, DOC, DOCX)\n"
              "⚠️ Максимальный размер файла: 10 МБ"),
        MessageInput(
            func=on_resume_uploaded,
            content_types=[ContentType.DOCUMENT]
        ),
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
               "📢 <b>Откуда узнали:</b> {how_found_text}{previous_dept_text}\n"
               "💼 <b>Опыт:</b> {experience}\n"
               "💭 <b>Мотивация:</b> {motivation}\n"
               "📄 <b>Резюме:</b> {resume_status}\n"
               "\n� <b>Приоритеты вакансий:</b>\n{priorities_summary}"),
        Row(
            Button(
                Const("📝 Изменить"),
                id="edit",
                on_click=on_edit_clicked
            ),
            Button(
                Const("✅ Подтвердить и отправить"),
                id="confirm",
                on_click=on_confirm_application
            )
        ),
        state=FirstStageSG.confirmation,
        getter=get_form_summary
    ),
    
    # Меню редактирования
    Window(
        Const("📝 Что вы хотите изменить?"),
        Column(
            Button(
                Format("👤 Изменить ФИО"),
                id="edit_full_name",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("🎓 Изменить университет"),
                id="edit_university", 
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("📚 Изменить курс"),
                id="edit_course",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("📱 Изменить телефон"),
                id="edit_phone",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("📧 Изменить email"),
                id="edit_email",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("📢 Изменить 'Откуда узнали'"),
                id="edit_how_found",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("💼 Изменить опыт"),
                id="edit_experience",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("💭 Изменить мотивацию"),
                id="edit_motivation",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("📄 Изменить резюме"),
                id="edit_resume",
                on_click=on_edit_field_clicked
            ),
            Button(
                Format("� Изменить выбор вакансий"),
                id="edit_department",
                on_click=on_edit_field_clicked
            )
        ),
        Button(
            Const("⬅️ Назад к подтверждению"),
            id="back_to_confirmation",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_menu,
        getter=get_edit_menu_data
    ),
    
    # Окна редактирования отдельных полей
    Window(
        Const("👤 Введите новое ФИО:"),
        TextInput(
            id="edit_full_name_input",
            on_success=on_edit_full_name_input
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_full_name
    ),
    
    Window(
        Const("🎓 Введите новый университет:"),
        TextInput(
            id="edit_university_input",
            on_success=on_edit_university_input
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_university
    ),
    
    Window(
        Const("📚 Выберите новый курс:"),
        Radio(
            Format("• {item[text]}"),
            Format("🔘 {item[text]}"),
            id="edit_course_radio",
            item_id_getter=lambda item: item["id"],
            items="courses",
            on_click=on_edit_course_selected
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        getter=get_course_options,
        state=FirstStageSG.edit_course
    ),
    
    Window(
        Const("📱 Введите новый номер телефона:"),
        TextInput(
            id="edit_phone_input",
            on_success=on_edit_phone_input
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_phone
    ),
    
    Window(
        Const("📧 Введите новый email:"),
        TextInput(
            id="edit_email_input",
            on_success=on_edit_email_input
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_email
    ),
    
    Window(
        Const("📢 Откуда вы узнали о КБК? (можно выбрать несколько вариантов)"),
        Multiselect(
            Format("✅ {item[text]}"),
            Format("☐ {item[text]}"),
            id="edit_how_found_multi",
            item_id_getter=lambda item: item["id"],
            items="how_found_options",
            on_state_changed=on_edit_how_found_state_changed
        ),
        Button(
            Const("Продолжить ➡️"),
            id="edit_how_found_continue",
            on_click=on_edit_how_found_continue
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        getter=get_edit_how_found_options,
        state=FirstStageSG.edit_how_found_kbk
    ),
    
    Window(
        Const("🏢 В каком отделе вы участвовали ранее?"),
        Radio(
            Format("• {item[text]}"),
            Format("🔘 {item[text]}"),
            id="edit_previous_dept_radio",
            item_id_getter=lambda item: item["id"],
            items="departments",
            on_click=on_edit_previous_department_selected
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        getter=get_departments_for_previous,
        state=FirstStageSG.edit_previous_department
    ),
    
    Window(
        Const("💼 Расскажите о своем опыте:"),
        TextInput(
            id="edit_experience_input",
            on_success=on_edit_experience_input
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_experience
    ),
    
    Window(
        Const("💭 Расскажите о своей мотивации:"),
        TextInput(
            id="edit_motivation_input",
            on_success=on_edit_motivation_input
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_motivation
    ),
    
    Window(
        Const("📄 Загрузите новое резюме (PDF, размер до 10 МБ):"),
        MessageInput(
            content_types=[ContentType.DOCUMENT],
            func=on_edit_resume_uploaded
        ),
        Button(
            Const("⬅️ Назад к меню"),
            id="back_to_edit_menu",
            on_click=on_back_to_confirmation
        ),
        state=FirstStageSG.edit_resume_upload
    ),
    
    # Успешная отправка
    Window(
        Const("🎉 <b>Заявка успешно отправлена!</b>\n\n"
              "Спасибо за интерес к КБК! Мы рассмотрим вашу заявку и свяжемся с вами в ближайшее время.\n\n"
              "Следите за обновлениями в нашем телеграм-канале!"),
        Button(Const("🏠 В главное меню"), id="go_to_menu", on_click=go_to_menu),
        state=FirstStageSG.success
    ),
    on_process_result=on_job_selection_result
)
