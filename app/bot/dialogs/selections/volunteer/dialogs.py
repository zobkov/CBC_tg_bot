"""Aiogram Dialog definitions for the volunteer selection flow."""

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, Row
from aiogram_dialog.widgets.text import Case, Const, Format

from .getters import get_confirmation_data, get_main_data
from .handlers import (
    on_additional_info_entered,
    on_confirm_no,
    on_confirm_yes,
    on_dates_double,
    on_dates_single,
    on_education_entered,
    on_email_entered,
    on_function_general,
    on_function_photo,
    on_function_translate,
    on_general_1_answer_entered,
    on_general_1_both,
    on_general_1_guest,
    on_general_1_no,
    on_general_1_volunteer,
    on_general_2_entered,
    on_general_3_entered,
    on_go_home,
    on_name_entered,
    on_phone_entered,
    on_photo_1_entered,
    on_photo_3_entered,
    on_photo_4_entered,
    on_photo_equipment_no,
    on_photo_equipment_yes,
    on_start_clicked,
    on_translate_1_entered,
    on_translate_3_1_entered,
    on_translate_3_2_entered,
    on_translate_4_entered,
    on_translate_cert_link_entered,
    on_translate_cert_no,
    on_translate_cert_yes,
    on_translate_experience_no,
    on_translate_experience_yes,
)
from .states import VolunteerSelectionSG

volunteer_dialog = Dialog(
    # ── MAIN ──────────────────────────────────────────────────────────────
    Window(
        Case(
            {
                False: Const(
                    """<b>Привет!</b>

Мы очень рады, что ты проявил(а) желание стать волонтёром и помогать нам в этом году.

С помощью этого бота ты сможешь пройти первый этап отбора на волонтёрство."""
                ),
                True: Const(
                    """✅ <b>Заявка уже отправлена!</b>

Мы вернемся с результатами первого этапа отбора <b>16 марта</b>.

Хочешь что-то уточнить? Не стесняйся и пиши нам, мы на связи: @savitsanastya @drkirna"""
                ),
            },
            selector="already_applied",
        ),
        Column(
            Button(Const("""✏️ Начать"""), id="vol_start", on_click=on_start_clicked),
            Cancel(Const("""⬅️ Назад""")),
        ),
        state=VolunteerSelectionSG.MAIN,
        getter=get_main_data,
    ),

    # ── CONFIRMATION ──────────────────────────────────────────────────────
    Window(
        Format(
            """<b>Мы нашли твои данные: </b>

ФИО: {vol_full_name}
Почта: {vol_email}
Образование: {vol_education}

Они верны?"""
        ),
        Column(
            Button(Const("""Да!"""), id="vol_confirm_yes", on_click=on_confirm_yes),
            Button(Const("""Нет. Надо заполнить заново"""), id="vol_confirm_no", on_click=on_confirm_no),
        ),
        state=VolunteerSelectionSG.confirmation,
        getter=get_confirmation_data,
    ),

    # ── NAME ──────────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Напиши, пожалуйста, свое ФИО</b>

Например: Иванов Иван Иванович"""
        ),
        TextInput(id="vol_name_input", on_success=on_name_entered),
        state=VolunteerSelectionSG.name,
    ),

    # ── EMAIL ─────────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Укажи свою почту</b>

Если ты из СПбГУ, то надо использовать корпоративную почту (должна заканчиваться на @spbu.ru, @student.spbu.ru или @gsom.spbu.ru)

Например: st118677@student.spbu.ru"""
        ),
        TextInput(id="vol_email_input", on_success=on_email_entered),
        state=VolunteerSelectionSG.email,
    ),

    # ── EDUCATION ─────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Напиши, где ты учишься</b>

Пиши в таком формате: СПбГУ, Юрфак, 3, 2027"""
        ),
        TextInput(id="vol_education_input", on_success=on_education_entered),
        state=VolunteerSelectionSG.education,
    ),

    # ── PHONE ─────────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Введи свой номер телефона</b>

Например: +79139736363 или 89216273306"""
        ),
        TextInput(id="vol_phone_input", on_success=on_phone_entered),
        state=VolunteerSelectionSG.phone,
    ),

    # ── VOLUNTEER_DATES ───────────────────────────────────────────────────
    Window(
        Const(
            """<b>Когда ты можешь помогать?</b>

1. Только в сам день форума (11 апреля 2026)
2. В день форума и могу помочь в день до КБК (10 и 11 апреля 2026)"""
        ),
        Column(
            Button(Const("""1. Только 11 апреля"""), id="vol_dates_single", on_click=on_dates_single),
            Button(Const("""2. 10 и 11 апреля"""), id="vol_dates_double", on_click=on_dates_double),
        ),
        state=VolunteerSelectionSG.volunteer_dates,
    ),

    # ── FUNCTION ──────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Какой функционал ты хочешь выполнять на КБК?</b>

1. Общий волонтёрский функционал
2. Фотографирование
3. Перевод"""
        ),
        Column(
            Button(Const("""1. Общий волонтёрский функционал"""), id="vol_func_general", on_click=on_function_general),
            Button(Const("""2. Фотографирование"""), id="vol_func_photo", on_click=on_function_photo),
            Button(Const("""3. Перевод"""), id="vol_func_translate", on_click=on_function_translate),
        ),
        state=VolunteerSelectionSG.function,
    ),

    # ── GENERAL_1 ─────────────────────────────────────────────────────────
    Window(
        Const("""<b>Посещал(а) ли ты когда-то КБК в качестве участника или волонтёра?</b>"""),
        Column(
            Button(Const("""1. Да, в качестве участника"""), id="vol_g1_guest", on_click=on_general_1_guest),
            Button(Const("""2. Да, в качестве волонтёра"""), id="vol_g1_volunteer", on_click=on_general_1_volunteer),
            Button(Const("""3. Да, как волонтёр и как участник"""), id="vol_g1_both", on_click=on_general_1_both),
            Button(Const("""4. Нет"""), id="vol_g1_no", on_click=on_general_1_no),
        ),
        state=VolunteerSelectionSG.general_1,
    ),

    # ── GENERAL_1_1 ───────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Поделись своим опытом участия.</b>

Что тебе понравилось, а что, по твоему мнению, можно улучшить?
<i>(обязательно ответь на обе части вопроса)</i>"""
        ),
        TextInput(id="vol_g1_1_input", on_success=on_general_1_answer_entered),
        state=VolunteerSelectionSG.general_1_1,
    ),

    # ── GENERAL_1_2 ───────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Поделись своим опытом волонтёрства.</b>

Что тебе понравилось, а что, по твоему мнению, можно улучшить?
<i>(обязательно ответь на обе части вопроса)</i>"""
        ),
        TextInput(id="vol_g1_2_input", on_success=on_general_1_answer_entered),
        state=VolunteerSelectionSG.general_1_2,
    ),

    # ── GENERAL_1_3 ───────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Поделись своим опытом участия/волонтёрства.</b>

Что тебе понравилось, а что, по твоему мнению, можно улучшить?
<i>(обязательно ответь на обе части вопроса)</i>"""
        ),
        TextInput(id="vol_g1_3_input", on_success=on_general_1_answer_entered),
        state=VolunteerSelectionSG.general_1_3,
    ),

    # ── GENERAL_2 ─────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Почему именно КБК?</b>

Почему тебе хочется стать волонтером на этом мероприятии?"""
        ),
        TextInput(id="vol_g2_input", on_success=on_general_2_entered),
        state=VolunteerSelectionSG.general_2,
    ),

    # ── GENERAL_3 ─────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Как ты считаешь, какие твои личностные качества будут наиболее полезны для работы в команде волонтёров КБК?</b>

Приведи примеры из своего опыта/жизни, когда твои качества помогали тебе решить проблему."""
        ),
        TextInput(id="vol_g3_input", on_success=on_general_3_entered),
        state=VolunteerSelectionSG.general_3,
    ),

    # ── PHOTO_1 ───────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Прикрепи ссылку на свое портфолио.</b>

(облачное хранилище, сайт, Instagram с работами)"""
        ),
        TextInput(id="vol_p1_input", on_success=on_photo_1_entered),
        state=VolunteerSelectionSG.photo_1,
    ),

    # ── PHOTO_2 ───────────────────────────────────────────────────────────
    Window(
        Const("""<b>Есть ли у тебя свое оборудование?</b>"""),
        Row(
            Button(Const("""Да"""), id="vol_p2_yes", on_click=on_photo_equipment_yes),
            Button(Const("""Нет"""), id="vol_p2_no", on_click=on_photo_equipment_no),
        ),
        state=VolunteerSelectionSG.photo_2,
    ),

    # ── PHOTO_3 ───────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Есть ли у тебя опыт фото/видеосъемки на мероприятиях?</b>

Расскажи, на каких."""
        ),
        TextInput(id="vol_p3_input", on_success=on_photo_3_entered),
        state=VolunteerSelectionSG.photo_3,
    ),

    # ── PHOTO_4 ───────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Как ты думаешь, какие ключевые моменты и эмоции важно запечатлеть фотографу на КБК, чтобы передать атмосферу форума?</b>"""
        ),
        TextInput(id="vol_p4_input", on_success=on_photo_4_entered),
        state=VolunteerSelectionSG.photo_4,
    ),

    # ── TRANSLATE_1 ───────────────────────────────────────────────────────
    Window(
        Const("""<b>Какой у тебя уровень китайского?</b>"""),
        TextInput(id="vol_t1_input", on_success=on_translate_1_entered),
        state=VolunteerSelectionSG.translate_1,
    ),

    # ── TRANSLATE_2 ───────────────────────────────────────────────────────
    Window(
        Const("""<b>Есть ли у тебя подтверждающий сертификат (HSK и др.)?</b>"""),
        Row(
            Button(Const("""Да"""), id="vol_t2_yes", on_click=on_translate_cert_yes),
            Button(Const("""Нет"""), id="vol_t2_no", on_click=on_translate_cert_no),
        ),
        state=VolunteerSelectionSG.translate_2,
    ),

    # ── TRANSLATE_2_CERTIFICATE ───────────────────────────────────────────
    Window(
        Const(
            """<b>Прикрепи ссылку на свой сертификат, пожалуйста.</b>

На облачное хранилище: Google Drive, Яндекс.Диск и т.п."""
        ),
        TextInput(id="vol_t2_cert_input", on_success=on_translate_cert_link_entered),
        state=VolunteerSelectionSG.translate_2_certificate,
    ),

    # ── TRANSLATE_3 ───────────────────────────────────────────────────────
    Window(
        Const("""<b>Был ли у тебя опыт общения на китайском языке?</b>"""),
        Row(
            Button(Const("""Да"""), id="vol_t3_yes", on_click=on_translate_experience_yes),
            Button(Const("""Нет"""), id="vol_t3_no", on_click=on_translate_experience_no),
        ),
        state=VolunteerSelectionSG.translate_3,
    ),

    # ── TRANSLATE_3_1 ─────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Расскажи подробнее, какой у тебя был опыт общения на китайском языке?</b>

(учеба, работа, путешествия)"""
        ),
        TextInput(id="vol_t3_1_input", on_success=on_translate_3_1_entered),
        state=VolunteerSelectionSG.translate_3_1,
    ),

    # ── TRANSLATE_3_2 ─────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Работал(а) ли ты когда-то с иностранными спикерами/гостями?</b>

Поделись своим опытом."""
        ),
        TextInput(id="vol_t3_2_input", on_success=on_translate_3_2_entered),
        state=VolunteerSelectionSG.translate_3_2,
    ),

    # ── TRANSLATE_4 ───────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Представь ситуацию: во время перевода ты не понял(а) или усомнился(ась) в точности сказанного говорящим.</b>

Как бы ты поступил(а)?"""
        ),
        TextInput(id="vol_t4_input", on_success=on_translate_4_entered),
        state=VolunteerSelectionSG.translate_4,
    ),

    # ── ADDITIONAL_INFORMATION_PROMPT ─────────────────────────────────────
    Window(
        Const(
            """<b>Есть ли что-то, что мы не спросили, но что важно, чтобы мы о тебе знали? Или у тебя есть вопросы к нам?</b>"""
        ),
        TextInput(id="vol_additional_input", on_success=on_additional_info_entered),
        state=VolunteerSelectionSG.additional_information_prompt,
    ),

    # ── END ───────────────────────────────────────────────────────────────
    Window(
        Const(
            """<b>Спасибо за твои ответы!</b> Мы вернемся с результатами первого этапа отбора <b>16 марта</b>.

Хочешь что-то уточнить? Не стесняйся и пиши нам, мы на связи: @savitsanastya @drkirna"""
        ),
        Cancel(Const("""🏠 В главное меню""")),
        state=VolunteerSelectionSG.END,
    ),
)
