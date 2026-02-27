"""Aiogram Dialog definition for the creative selection (casting) flow."""

from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, Multiselect, Radio, Row, Start
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Multi

from .getters import (
    get_confirmation_data,
    get_creative_intro_media,
    get_directions,
    get_duration_options,
    get_fair_role_options,
    get_frequency_options,
    get_main_text,
    get_selected_fair_roles,
    get_timeslot_options,
)
from .handlers import (
    name_check,
    on_back_to_direction_selection,
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
from app.bot.dialogs.guest.states import GuestMenuSG

_SUCCESS_TEXT = (
    "🎉 <b>Заявка успешно отправлена!</b>\n\n"
    "Спасибо за участие в кастинге форума КБК 2026. Мы рассмотрим твою заявку и свяжемся с тобой в ближайшее время.\n\n"
    "Следи за обновлениями в нашем канале и боте!"
)

_FAIR_TEXT = """<b>Ярмарка культруы</b>
Отметь роли, в которых ты хотел бы себя попробовать:
(можно выбрать несколько)

1. <b>Интерактив: Колесо удачи</b>
Здесь тебе предстоит делиться с гостями предсказаниями на день в зависимости от выпавшего элемента. Небольшой, но классный интерактив!

2. <b>Интерактив: Гонки драконов (мини-версия Dragon Boat)</b>
Тебе предстоит проводить гонки мини-лодок в виде драконов: твоя задача — следить за ходом соревнований и рассказывать участникам об истории и традициях фестиваля драконьих лодок в Китае.

3. <b>Интерактив: сбор аромасаше</b>
Здесь ты выступишь в роли продавца трав и целителя. Твоя задача - рассказать о свойствах представленных ингредиентов и подсказать, какой сбор поможет обрести спокойствие, а какой — разбогатеть! Не переживай, всю информацию мы тебе предоставим.

4. <b>Интерактив: Китайское гадание (по книге перемен И Цзин и монетам)</b>
Участник загадывает вопрос, бросает монеты и чертит на бумаге гексаграмму. Мастер находит её значение в книге и даёт ответ. 

5. <b>Мастер-класс: Вышивка небольших рисунков в китайской стилистике</b>
Не переживай, тебе не придется осваивать сложные техники — мы вместе подберём рисунки, с которыми легко справятся и ведущий, и гости.

6. <b>Мастер-класс: Создание подвески «Музыка ветра»</b>
Твоя задача — помочь гостям собрать подвески-напоминания о Китае и КБК. Ничего сложного — просто соединяем готовые элементы в единую композицию.

7. <b>Мастер-класс: Создание металлических амулетов с отчеканенными символами</b>
Здесь ты будешь помогать отчеканивать иероглифы и символы на металлических амулетах. Твоя главная задача — раскрывать их значение для участников. Техника простая, так что с ней справится каждый. 

8. <b>Мастер-класс: Роспись масок из Пекинской оперы</b>
Твоя задача — погрузить гостей в мир китайской оперы через маски. Расскажешь, что означают цвета и символы, а раскрашивать помогут уже готовые линии. Если захочется импровизации — поддержи и подскажи, как сделать маску по-настоящему особенной.
"""

creative_selection_dialog = Dialog(
    # Entry point / Main window
    Window(
        DynamicMedia("media"),
        Format("{intro_text}"),
        Column(
            Button(Const("📝 Подать заявку"), id="start_application", on_click=on_start_clicked),
            Start(Const("🏠 Назад"), id="cancel_main", mode=StartMode.RESET_STACK, state=GuestMenuSG.MAIN),
        ),
        state=CreativeSelectionSG.MAIN,
        getter=[get_main_text, get_creative_intro_media],
    ),
    # Common questions
    Window(
        Const("<b>Как тебя зовут?</b>\n\nНапиши свою фамилию, имя и отчество полностью."),
        TextInput(
            id="creative_name",
            on_success=on_name_entered,
            on_error=on_name_error,
            type_factory=name_check,
        ),
        state=CreativeSelectionSG.name,
    ),
    Window(
        Const("<b>Как с тобой можно связаться?</b> (ВК/Телеграм)\n\nНапример: @username или vk.com/username"),
        TextInput(
            id="creative_contact",
            on_success=on_contact_entered,
        ),
        state=CreativeSelectionSG.contact,
    ),
    Window(
        Const("<b>Электронная почта</b>\n\nУкажи действующий e-mail."),
        TextInput(
            id="creative_email",
            on_success=on_email_entered,
        ),
        state=CreativeSelectionSG.email,
    ),
    Window(
        Const(
            "<b>Университет, факультет, курс, год выпуска</b>\n\n"
            "Пример: СПбГУ, ВШМ, 3, 2027"
        ),
        TextInput(
            id="creative_university",
            on_success=on_university_entered,
        ),
        state=CreativeSelectionSG.university,
    ),
    # Direction selection (branch point)
    Window(
        Const(
            "<b>В каком направлении ты хочешь участвовать?</b>\n\n" \
            "• Церемония открытия и закрытия (в роли актёра)\n" \
            "• Ярмарка культуры (проведение мастер-классов и интерактивов)"
        ),
        Column(
            Radio(
                Format("{item[text]}"),
                Format("{item[text]}"),
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
    # First question after selecting ceremony: check MD attendance ability
    Window(
        Multi(
            Const("<b>Сможешь ли ты посещать очные репетиции, которые будут проводиться в Михайловской Даче?</b>"),
            Const("\n<i>МД: Санкт-Петербургское ш., 109, Петергоф</i>"),
            sep="\n",
        ),
        Column(
            Button(Const("Смогу"), id="can_attend", on_click=on_rehearsal_attendance_selected),
            Button(Const("Не смогу"), id="cannot_attend", on_click=on_rehearsal_attendance_selected),
        ),
        state=CreativeSelectionSG.ceremony_rehearsal_attendance,
    ),
    # MD attendance required notice (shown if user cannot attend)
    Window(
        Const(
            "К сожалению, для участия в церемонии открытия посещение репетиций в Михайловской даче является обязательным.\n\n"
            "Если у тебя нет возможности посещать очные репетиции, мы можем предложить тебе попробовать себя в другом направлении в качестве ведущего мастер-классов!"
        ),
        Column(
            Button(
                Const("← Вернуться к выбору направления"),
                id="back_to_direction",
                on_click=on_back_to_direction_selection,
            ),
            Cancel(Const("❌ Отменить заявку"), id="cancel_md_notice"),
        ),
        state=CreativeSelectionSG.ceremony_md_required_notice,
    ),
    # Continue ceremony application (if user can attend)
    Window(
        Const(
            "<b>Церемония открытия и закрытия</b>\n\n"
            "Если есть сценический опыт, расскажи о нем поподробнее."
        ),
        TextInput(
            id="ceremony_stage_exp",
            on_success=on_ceremony_stage_exp_entered,
        ),
        state=CreativeSelectionSG.ceremony_stage_experience,
    ),
    Window(
        Const("<b>Расскажи о своей мотивации для участия.</b>"),
        TextInput(
            id="ceremony_motivation",
            on_success=on_ceremony_motivation_entered,
        ),
        state=CreativeSelectionSG.ceremony_motivation,
    ),
    Window(
        Const("<b>Сколько раз в неделю ты готов посещать репетиции?</b>"),
        Column(
            Radio(
                Format("{item[text]}"),
                Format("{item[text]}"),
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
        Const("<b>Сколько времени ты готов выделять на одну репетицию?</b>"),
        Column(
            Radio(
                Format("{item[text]}"),
                Format("{item[text]}"),
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
            "<b>В какое время ты готов посещать репетиции в МД?</b>\n\n"
            "Можно выбрать несколько вариантов, но не менее одного:"
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
        ),
        state=CreativeSelectionSG.ceremony_rehearsal_timeslots,
        getter=get_timeslot_options,
    ),
    Window(
        Multi(
            Const("<b>При желании можешь прикрепить ссылку на облако с фото/видео.</b>"),
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
        # pseudo photo gallery
        Multi(
            Const(_FAIR_TEXT),
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
        ),
        state=CreativeSelectionSG.fair_role_selection,
        getter=get_fair_role_options,
    ),
    Window(
        Multi(
            Const("<b>Почему ты выбрал именно эту роль (эти роли)?</b>"),
            Const("\n\n\n<i>Выбранные роли:</i>"),
            Format("\n{selected_roles}"),
            sep="",
        ),
        TextInput(
            id="fair_role_motivation",
            on_success=on_fair_motivation_entered,
        ),
        state=CreativeSelectionSG.fair_role_motivation,
        getter=get_selected_fair_roles,
    ),
    Window(
        Const(
            "<b>Если у тебя есть опыт в выбранной роли или любой другой опыт в проведении мастер-классов/активностей, расскажи о них поподробнее.</b>"
        ),
        TextInput(
            id="fair_role_experience",
            on_success=on_fair_experience_entered,
        ),
        state=CreativeSelectionSG.fair_role_experience,
    ),
    Window(
        Multi(
            Const("<b>Если хочешь поделиться своими работами или изделиями, можешь прикрепить ссылку на облако.</b>"),
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
        Cancel(Const("🏠 В главное меню"),id="go_home"),
        state=CreativeSelectionSG.success,
    ),
)
