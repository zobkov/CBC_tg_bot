"""Aiogram Dialog definition for the creative selection (casting) flow."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, Multiselect, Radio, Row
from aiogram_dialog.widgets.text import Const, Format, Multi

from .getters import (
    get_confirmation_data,
    get_directions,
    get_duration_options,
    get_fair_role_options,
    get_frequency_options,
    get_timeslot_options,
)
from .handlers import (
    name_check,
    on_ceremony_cloud_link_entered,
    on_ceremony_motivation_entered,
    on_ceremony_stage_exp_entered,
    on_contact_entered,
    on_direction_selected,
    on_duration_selected,
    on_email_entered,
    on_fair_cloud_link_entered,
    on_fair_experience_entered,
    on_fair_motivation_entered,
    on_fair_roles_changed,
    on_fair_roles_confirmed,
    on_frequency_selected,
    on_go_home,
    on_name_entered,
    on_name_error,
    on_rehearsal_attendance_selected,
    on_skip_ceremony_cloud,
    on_skip_fair_cloud,
    on_start_clicked,
    on_submit_application,
    on_timeslots_changed,
    on_timeslots_confirmed,
    on_university_entered,
)
from .states import CreativeSelectionSG

_INTRO_TEXT = (
    "🎭 <b>Заявка на кастинг форума «Китай Бизнес Культура» 2026</b>\n\n"
    "Добро пожаловать на кастинг для форума КБК!\n\n"
    "Тебе предстоит выбрать одно из направлений:\n"
    "• Церемония открытия (в роли актёра)\n"
    "• Ярмарка культуры (проведение мастер-классов и интерактивов)\n\n"
    "Заполнение займет около 5-7 минут. Удачи!"
)

_SUCCESS_TEXT = (
    "🎉 <b>Заявка успешно отправлена!</b>\n\n"
    "Спасибо за участие в кастинге форума КБК 2026.\n"
    "Мы рассмотрим твою заявку и свяжемся с тобой в ближайшее время.\n\n"
    "Следи за обновлениями в нашем канале!"
)

creative_selection_dialog = Dialog(
    # Entry point / Main window
    Window(
        Const(_INTRO_TEXT),
        Column(
            Button(Const("📝 Начать заявку"), id="start_application", on_click=on_start_clicked),
            Cancel(Const("🏠 Назад"), id="cancel_main"),
        ),
        state=CreativeSelectionSG.MAIN,
    ),
    # Common questions
    Window(
        Const("Как тебя зовут?\n\nНапиши свою фамилию, имя и отчество полностью."),
        TextInput(
            id="creative_name",
            on_success=on_name_entered,
            on_error=on_name_error,
            type_factory=name_check,
        ),
        state=CreativeSelectionSG.name,
    ),
    Window(
        Const("Как с тобой можно связаться? (ВК/Телеграм)\n\nНапример: @username или vk.com/username"),
        TextInput(
            id="creative_contact",
            on_success=on_contact_entered,
        ),
        state=CreativeSelectionSG.contact,
    ),
    Window(
        Const("Электронная почта\n\nУкажи действующий e-mail."),
        TextInput(
            id="creative_email",
            on_success=on_email_entered,
        ),
        state=CreativeSelectionSG.email,
    ),
    Window(
        Const(
            "Университет, факультет\n\n"
            "Пример: <b>СПбГУ, ВШМ</b> или <b>СПбГУ, Философский факультет</b>"
        ),
        TextInput(
            id="creative_university",
            on_success=on_university_entered,
        ),
        state=CreativeSelectionSG.university,
    ),
    # Direction selection (branch point)
    Window(
        Const("В каком направлении ты хочешь участвовать?"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="direction_radio",
                item_id_getter=lambda item: item["id"],
                items="directions",
                on_click=on_direction_selected,
            ),
        ),
        state=CreativeSelectionSG.direction_selection,
        getter=get_directions,
    ),
    # Ceremony branch
    Window(
        Const(
            "<b>Церемония открытия</b>\n\n"
            "В случае наличия сценического опыта, расскажи о нем поподробнее."
        ),
        TextInput(
            id="ceremony_stage_exp",
            on_success=on_ceremony_stage_exp_entered,
        ),
        state=CreativeSelectionSG.ceremony_stage_experience,
    ),
    Window(
        Const("Расскажи о своей мотивации для участия."),
        TextInput(
            id="ceremony_motivation",
            on_success=on_ceremony_motivation_entered,
        ),
        state=CreativeSelectionSG.ceremony_motivation,
    ),
    Window(
        Multi(
            Const("Сможешь ли ты посещать очные репетиции, которые будут проводиться в Михайловской Даче?"),
            Const("\n<i>МД: Санкт-Петербургское ш., 109, Петергоф</i>"),
            sep="\n",
        ),
        Column(
            Button(Const("Смогу"), id="can_attend", on_click=on_rehearsal_attendance_selected),
            Button(Const("Не смогу"), id="cannot_attend", on_click=on_rehearsal_attendance_selected),
        ),
        state=CreativeSelectionSG.ceremony_rehearsal_attendance,
    ),
    Window(
        Const("Сколько раз в неделю ты готов посещать репетиции?"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="frequency_radio",
                item_id_getter=lambda item: item["id"],
                items="frequency_options",
                on_click=on_frequency_selected,
            ),
        ),
        state=CreativeSelectionSG.ceremony_rehearsal_frequency,
        getter=get_frequency_options,
    ),
    Window(
        Const("Сколько времени ты готов выделять на одну репетицию?"),
        Column(
            Radio(
                Format("🔘 {item[text]}"),
                Format("⚪ {item[text]}"),
                id="duration_radio",
                item_id_getter=lambda item: item["id"],
                items="duration_options",
                on_click=on_duration_selected,
            ),
        ),
        state=CreativeSelectionSG.ceremony_rehearsal_duration,
        getter=get_duration_options,
    ),
    Window(
        Const(
            "В какое время ты готов посещать репетиции в МД?\n\n"
            "Можно выбрать несколько вариантов:"
        ),
        Column(
            Multiselect(
                Format("✅ {item[text]}"),
                Format("☐ {item[text]}"),
                id="timeslots_multiselect",
                item_id_getter=lambda item: item["id"],
                items="timeslot_options",
                min_selected=1,
                on_state_changed=on_timeslots_changed,
            ),
        ),
        Button(
            Const("➡️ Далее"),
            id="continue_timeslots",
            on_click=on_timeslots_confirmed,
            when="has_timeslots",
        ),
        state=CreativeSelectionSG.ceremony_rehearsal_timeslots,
        getter=get_timeslot_options,
    ),
    Window(
        Multi(
            Const("При желании можешь прикрепить ссылку на облако с фото/видео."),
            Const("\n<i>Укажи ссылку на Google Drive, Яндекс.Диск или другое облачное хранилище.</i>"),
            Const("\n\nМожешь пропустить этот шаг."),
            sep="\n",
        ),
        TextInput(
            id="ceremony_cloud_link",
            on_success=on_ceremony_cloud_link_entered,
        ),
        Button(
            Const("⏭️ Пропустить"),
            id="skip_ceremony_cloud",
            on_click=on_skip_ceremony_cloud,
        ),
        state=CreativeSelectionSG.ceremony_cloud_link,
    ),
    # Fair branch
    Window(
        Multi(
            Const("<b>Ярмарка культуры</b>\n\n"),
            Const("Отметь роли, в которых ты хотел бы себя попробовать.\n"),
            Const("Можно выбрать несколько:"),
            sep="",
        ),
        Column(
            Multiselect(
                Format("✅ {item[text]}"),
                Format("☐ {item[text]}"),
                id="fair_roles_multiselect",
                item_id_getter=lambda item: item["id"],
                items="fair_role_options",
                min_selected=1,
                on_state_changed=on_fair_roles_changed,
            ),
        ),
        Button(
            Const("➡️ Далее"),
            id="continue_fair_roles",
            on_click=on_fair_roles_confirmed,
            when="has_fair_roles",
        ),
        state=CreativeSelectionSG.fair_role_selection,
        getter=get_fair_role_options,
    ),
    Window(
        Const("Почему ты выбрал именно эту роль (эти роли)?"),
        TextInput(
            id="fair_role_motivation",
            on_success=on_fair_motivation_entered,
        ),
        state=CreativeSelectionSG.fair_role_motivation,
    ),
    Window(
        Const(
            "Если у тебя есть опыт в выбранной роли или любой другой опыт в проведении "
            "мастер-классов/активностей, расскажи о них поподробнее."
        ),
        TextInput(
            id="fair_role_experience",
            on_success=on_fair_experience_entered,
        ),
        state=CreativeSelectionSG.fair_role_experience,
    ),
    Window(
        Multi(
            Const("Если хочешь поделиться своими работами или изделиями, можешь прикрепить ссылку на облако."),
            Const("\n<i>Укажи ссылку на Google Drive, Яндекс.Диск или другое облачное хранилище.</i>"),
            Const("\n\nМожешь пропустить этот шаг."),
            sep="\n",
        ),
        TextInput(
            id="fair_cloud_link",
            on_success=on_fair_cloud_link_entered,
        ),
        Button(
            Const("⏭️ Пропустить"),
            id="skip_fair_cloud",
            on_click=on_skip_fair_cloud,
        ),
        state=CreativeSelectionSG.fair_cloud_link,
    ),
    # Confirmation
    Window(
        Multi(
            Const("✅ <b>Проверь  свои данные перед отправкой</b>\n"),
            Format("👤 <b>ФИО:</b> {name}"),
            Format("📱 <b>Контакт:</b> {contact}"),
            Format("📧 <b>Email:</b> {email}"),
            Format("🏫 <b>Университет:</b> {university}"),
            Format("🎯 <b>Направление:</b> {direction}\n"),
            Format("{branch_details}\n"),
            Const("Всё верно?"),
            sep="\n",
        ),
        Row(
            Button(Const("✅ Отправить"), id="submit", on_click=on_submit_application),
            Cancel(Const("❌ Отменить"), id="cancel_confirm"),
        ),
        state=CreativeSelectionSG.confirmation,
        getter=get_confirmation_data,
    ),
    # Success
    Window(
        Const(_SUCCESS_TEXT),
        Button(Const("🏠 В главное меню"), id="go_home", on_click=on_go_home),
        state=CreativeSelectionSG.success,
    ),
)
