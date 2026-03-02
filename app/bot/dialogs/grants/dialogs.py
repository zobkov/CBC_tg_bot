"""Grants section dialog — all windows and the Dialog object."""
from __future__ import annotations

import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Group,
    Row,
    Select,
    Start,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.link_preview import LinkPreview

from app.bot.dialogs.grants.getters import get_lesson_data, get_mentor_data
from app.bot.dialogs.grants.handlers import (
    on_back_from_course,
    on_back_from_course_gsom,
    on_course_general_clicked,
    on_course_gsom_clicked,
    on_lesson_selected,
)
from app.bot.dialogs.grants.states import GrantsSG
from app.bot.dialogs.settings.states import SettingsSG

# ---------------------------------------------------------------------------
# MAIN_GENERAL
# ---------------------------------------------------------------------------
_MAIN_GENERAL_TEXT = """🏆 <b>О конкурсе Росмолодёжь.Гранты:</b>

В 2026 году форум КБК становится площадкой Всероссийского конкурса «Росмолодёжь.Гранты», где участники могут получить поддержку для развития своих инициатив.

➡️ <b>Курс по социальному проектированию:</b> 2–26 марта 2026
➡️ <b>Регистрация на конкурс:</b> 3 марта – 3 апреля, 10:00 МСК
➡️ <a href="https://myrosmol.ru/events/f70b4bd4-5df5-4794-b5b1-7ab67b1ca048">Подробная информация</a>
➡️ <a href="https://myrosmol.ru/grants/upload/3f62da3c4c9e4ee889eeb1cb4ff98dc1.pdf">Положение о конкурсе</a> 

Мы верим в тебя и твои проекты — продолжай действовать, ты на верном пути!
"""

# ---------------------------------------------------------------------------
# MAIN_GSOM
# ---------------------------------------------------------------------------
_MAIN_GSOM_TEXT = (
    "<b>Личный кабинет Центра развития проектов ВШМ СПбГУ</b>\n\n"
    "Личный кабинет создан, чтобы помочь тебе <b>без лишних сложностей "
    "подготовить и успешно защитить свой проект</b>.\n\n"
    "Здесь собрана вся ключевая информация:\n"
    "• образовательный курс;\n"
    "• грантовый конкурс;\n"
    "• работа с персональным менеджером.\n\n"
    "Всё в одном месте — чтобы ты мог сосредоточиться на главном и "
    "уверенно двигаться к результату."
)

# ---------------------------------------------------------------------------
# COURSE 
# ---------------------------------------------------------------------------
_COURSE_TEXT = """📚 <b>Образовательный курс:</b>

Чтобы ты мог превратить свою идею или проект в сильную грантовую заявку, мы вместе с ведущими экспертами Росмолодёжь.Гранты подготовили образовательный курс по социальному проектированию. Курс состоит из <b>6 вебинаров</b> и пройдёт <b>с 2 по 26 марта 2026 года</b>.

Подробности — в карточках выше. Чтобы ничего не пропустить, <a href="https://t.me/+fX1cEERQRy01MGZi">присоединяйся к чату участников конкурса</a>!
"""

# ---------------------------------------------------------------------------
# FAQ  
# ---------------------------------------------------------------------------
_FAQ_TEXT = """❓<b>FAQ</b>:

Здесь мы собрали <b>ответы на самые частые вопросы</b> о грантовом конкурсе.

Если не найдёшь нужный ответ — заходи <a href="https://t.me/+fX1cEERQRy01MGZi">в общий чат участников конкурса</a>. Мы обязательно поможем и подскажем.

➡️ <b>Максимальный грант:</b> до 1 млн руб.
➡️ <b>Кто может участвовать:</b> 16–35 лет, со всех регионов РФ
➡️ <b>Направления проектов:</b> занятость, малые города, культура, экология, спорт, наука, технологии, медиа, межкультурный диалог, добровольчество, атомная отрасль
➡️ <b>Подача заявок:</b> 11 марта, 12:00 — 6 апреля, 23:59 (МСК)
➡️ <b>Форум и защиты:</b> 11 апреля 2026 года, ВШМ СПбГУ, кампус «Михайловская дача»
➡️ <a href="https://t.me/+SgTMf6ZsjFxiMzRi">Чат с участниками конкурса</a>
➡️ <a href="https://t.me/forumcbc/639?single">Образовательный курс</a>
"""

# ---------------------------------------------------------------------------
# MENTOR
# ---------------------------------------------------------------------------
_MENTOR_TEXT = """<b>Работа с ментором</b>

Это пространство создано для индивидуальной работы с твоим ментором.

<b>Работа проходит по следующему формату:</b>
1. Всего доступно 11 уроков.
2. Перед звонком с ментором тебе необходимо изучить материалы текущего урока.
3. По итогам изучения нужно подготовить набросок / черновик (идеи, вопросы, структуру).
4. На созвоне ментор: поможет доработать материал, направит мысли в нужную сторону, даст подробную обратную связь.
5. После доработки и согласования результата менторм откроет доступ к следующему уроку.

<b>Доступные уроки:</b> {num_open_lessons} / {total_lessons}
<b>Твой ментор:</b> {mentor_contacts}

<b>Список уроков:</b>
{lessons_list}
"""

# ---------------------------------------------------------------------------
# LESSON
# ---------------------------------------------------------------------------
_LESSON_TEXT = (
    "<b>{lesson_name}</b>\n\n"
    "{lesson_description}\n\n"
    "Ниже ты найдёшь ссылку на <b>Яндекс.Диск</b> с образовательными "
    "материалами к этому уроку.\n\n"
    "Внимательно ознакомься с ними, а затем <b>свяжись с ментором</b>, чтобы "
    "проработать ответы на вопросы и разобрать всё, что осталось непонятным."
)


# ===========================================================================
# Dialog
# ===========================================================================
grants_dialog = Dialog( 
    # -------------------------------------------------------------------
    # 1. MAIN_GENERAL
    # -------------------------------------------------------------------
    Window(
        StaticMedia(path="app/bot/assets/images/grants/1.png"),
        Const(_MAIN_GENERAL_TEXT),
        Button(
            Const("📚 Образовательный курс"),
            id="course_general",
            on_click=on_course_general_clicked,
        ),
        SwitchTo(
            Const("❓ FAQ"),
            id="faq_general",
            state=GrantsSG.FAQ,
        ),
        Row(
            Start(
                Const("⚙️ Помощь и настройки"),
                id="settings_general",
                state=SettingsSG.MAIN,
            ),
            Cancel(Const("⬅️ Назад")),
        ),
        state=GrantsSG.MAIN_GENERAL,
    ),

    # -------------------------------------------------------------------
    # 2. MAIN_GSOM
    # -------------------------------------------------------------------
    Window(
        StaticMedia(path="app/bot/assets/images/grants/1.png"),
        Const(_MAIN_GSOM_TEXT),
        Button(
            Const("📚 Образовательный курс"),
            id="course_gsom",
            on_click=on_course_gsom_clicked,
        ),
        SwitchTo(
            Const("❓ FAQ"),
            id="faq_gsom",
            state=GrantsSG.FAQ_GSOM,
        ),
        SwitchTo(
            Const("👨‍🏫 Работа с ментором"),
            id="mentor_gsom",
            state=GrantsSG.MENTOR,
        ),
        Row(
            Start(
                Const("⚙️ Помощь и настройки"),
                id="settings_gsom",
                state=SettingsSG.MAIN,
            ),
            Cancel(Const("⬅️ Назад")),
        ),
        state=GrantsSG.MAIN_GSOM,
    ),

    # -------------------------------------------------------------------
    # 1.2 COURSE (general branch)
    # -------------------------------------------------------------------
    Window(
        Const(_COURSE_TEXT),
        LinkPreview(is_disabled=True),
        Button(Const("⬅️ Назад"), id="back_course", on_click=on_back_from_course),
        state=GrantsSG.COURSE,
    ),

    # -------------------------------------------------------------------
    # 1.3 FAQ (general branch)
    # -------------------------------------------------------------------
    Window(
        Const(_FAQ_TEXT),
        LinkPreview(is_disabled=True),
        SwitchTo(Const("⬅️ Назад"), id="back_faq", state=GrantsSG.MAIN_GENERAL),
        state=GrantsSG.FAQ,
    ),

    # -------------------------------------------------------------------
    # 2.2 COURSE_GSOM
    # -------------------------------------------------------------------
    Window(
        Const(_COURSE_TEXT),
        Button(Const("⬅️ Назад"), id="back_course_gsom", on_click=on_back_from_course_gsom),
        state=GrantsSG.COURSE_GSOM,
    ),

    # -------------------------------------------------------------------
    # 2.3 FAQ_GSOM
    # -------------------------------------------------------------------
    Window(
        Const(_FAQ_TEXT),
        LinkPreview(is_disabled=True),
        SwitchTo(Const("⬅️ Назад"), id="back_faq_gsom", state=GrantsSG.MAIN_GSOM),
        state=GrantsSG.FAQ_GSOM,
    ),

    # -------------------------------------------------------------------
    # 2.4 MENTOR
    # -------------------------------------------------------------------
    Window(
        Format(_MENTOR_TEXT),
        Group(
            Select(
                Format("{item[0]}"),
                id="lesson_select",
                item_id_getter=operator.itemgetter(1),
                items="open_lessons",
                on_click=on_lesson_selected,
            ),
            width=1,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_mentor", state=GrantsSG.MAIN_GSOM),
        getter=get_mentor_data,
        state=GrantsSG.MENTOR,
    ),

    # -------------------------------------------------------------------
    # 2.5 LESSON
    # -------------------------------------------------------------------
    Window(
        Format(_LESSON_TEXT),
        Url(
            Const("🔗 Ссылка на урок"),
            Format("{lesson_url}"),
            id="lesson_url_btn",
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_lesson", state=GrantsSG.MENTOR),
        getter=get_lesson_data,
        state=GrantsSG.LESSON,
    ),
)
