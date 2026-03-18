"""Aiogram Dialog definition for volunteer selection part 2."""

from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Column, Row, Start, SwitchTo
from aiogram_dialog.widgets.text import Const

from app.bot.dialogs.main.states import MainMenuSG
from .getters import get_main_data
from .handlers import (
    on_proceed_to_timer,
    on_start_yes,
    on_start_no,
    on_q1_selected,
    on_q2_entered,
    on_q3_entered,
    on_q4_entered,
    on_q5_entered,
    on_q6_entered,
    on_q7_yes,
    on_q7_no,
    on_q7_experience_yes,
    on_q7_experience_no,
    on_q7_route_entered,
    on_video_proceed,
    on_wrong_content_type,
    on_vq1,
    on_vq2,
    on_vq3,
)
from .states import VolSelPart2SG

_ALREADY_DONE_TEXT = (
    "✅ <b>Ты уже прошёл(-а) второй этап отбора!</b>\n\n"
    "Спасибо за ответы — мы проверим их и сообщим результаты в ближайшее время.\n\n"
    "Ориентировочное время: 30 марта.\n\n"
    "Следи за обновлениями в боте и подписывайся на наш основной канал: https://t.me/forumcbc\n"
    "Остались вопросы? Пиши: @savitsanastya @drkirna"
)

_NO_PART1_TEXT = (
    "⚠️ <b>Второй этап недоступен</b>\n\n"
    "Заявка первого этапа не найдена. Обратись к организаторам: @savitsanastya @drkirna"
)

volunteer_selection_part2_dialog = Dialog(

    # ── MAIN / guard ──────────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Привет!</b>\n\n"
            "Поздравляем тебя с успешным прохождением первого этапа отбора!\n\n"
            "Ты отлично ответил(-а) на наши вопросы, и мы предлагаем тебе пройти небольшое "
            "тестовое задание, которое поможет нам лучше понять твою мотивацию участия и "
            "узнать побольше о тебе.",
            when="can_start",
        ),
        Const(_ALREADY_DONE_TEXT, when="already_completed"),
        Const(_NO_PART1_TEXT, when="no_application"),
        Button(
            Const("Далее"),
            id="vsp2_proceed",
            on_click=on_proceed_to_timer,
            when="can_start",
        ),
        Start(
            Const("⬅️ Назад"),
            id="vsp2_back_home",
            state=MainMenuSG.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        state=VolSelPart2SG.MAIN,
        getter=get_main_data,
    ),

    # ── Timer warning ─────────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Важно!</b> Тестирование ограничено по времени: оно длится <b>35 минут</b>. "
            "Поэтому, когда будешь проходить его, убедись, что тебя ничего не отвлекает.\n\n"
            "Тестирование состоит из заданий формата выбора правильного варианта ответа, "
            "развернутых ответов и небольшого интервью (тебе нужно записать кружочки в Телеграме). "
            "Интервью будет в самом конце (3 вопроса), поэтому удели достаточно времени для его прохождения.\n\n"
            "Мы не даём строгих ограничений по времени на каждый вопрос, чтобы ты мог(-ла) спокойно "
            "выполнить все задания в рамках общего временного лимита. Поэтому ты можешь самостоятельно "
            "решить, на какие вопросы нужно уделить больше времени.\n\n"
            "Мы надеемся на твою искренность и добросовестность. Мы не приветствуем использование ИИ "
            "для выполнения данного задания: нам не важен идеальный ответ, сгенерированный нейросетью, "
            "а твоё умение размышлять и делиться своим опытом.\n\n"
            "<b>Готов(-а) ли ты приступить к тестированию?</b>"
        ),
        Row(
            Button(Const("Да"), id="vsp2_ready_yes", on_click=on_start_yes),
            Button(Const("Нет"), id="vsp2_ready_no", on_click=on_start_no),
        ),
        state=VolSelPart2SG.timer_warning,
    ),

    # ── Q1 – КБК ordinal ─────────────────────────────────────────────────────
    Window(
        Const("<b>Вопрос 1/7</b>\n\nКакой по счёту КБК в этом году?"),
        Column(
            Button(Const("1ый"), id="q1_1", on_click=on_q1_selected),
            Button(Const("2ой"), id="q1_2", on_click=on_q1_selected),
            Button(Const("3ий"), id="q1_3", on_click=on_q1_selected),
            Button(Const("4ый"), id="q1_4", on_click=on_q1_selected),
            Button(Const("5ый"), id="q1_5", on_click=on_q1_selected),
        ),
        state=VolSelPart2SG.q1,
    ),

    # ── Q2 – КБК date ────────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Вопрос 2/7</b>\n\n"
            "Когда проводится КБК в этом году?\n"
            "(Впиши дату и месяц в формате «25 декабря»)"
        ),
        TextInput(id="vsp2_q2_input", on_success=on_q2_entered),
        state=VolSelPart2SG.q2,
    ),

    # ── Q3 – КБК theme ───────────────────────────────────────────────────────
    Window(
        Const("<b>Вопрос 3/7</b>\n\nКакая тематика КБК в этом году?"),
        TextInput(id="vsp2_q3_input", on_success=on_q3_entered),
        state=VolSelPart2SG.q3,
    ),

    # ── Q4 – Team experience ──────────────────────────────────────────────────
    Window(
        Const(
            "<b>Вопрос 4/7</b>\n\n"
            "Многие из нас имеют опыт работы в команде, и нередко у нас могут возникать "
            "разногласия с сокомандниками.\n\n"
            "1. Опиши свой опыт работы в команде.\n"
            "2. Как ты обычно решаешь спорные ситуации при работе с другими людьми?"
        ),
        TextInput(id="vsp2_q4_input", on_success=on_q4_entered),
        state=VolSelPart2SG.q4,
    ),

    # ── Q5 – Badge case ───────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Вопрос 5/7</b>\n\n"
            "Представь, что тебе поручено встречать гостей и выдавать бейджики, и в процессе "
            "понимаешь, что не хватает бейджа для очень важного гостя. Напиши, что ты будешь делать."
        ),
        TextInput(id="vsp2_q5_input", on_success=on_q5_entered),
        state=VolSelPart2SG.q5,
    ),

    # ── Q6 – Foreign guest case ───────────────────────────────────────────────
    Window(
        Const(
            "<b>Вопрос 6/7</b>\n\n"
            "КБК – интернациональное мероприятие. Представь, что ты видишь иностранного гостя, "
            "который потерялся и что-то ищет. Опиши твои действия."
        ),
        TextInput(id="vsp2_q6_input", on_success=on_q6_entered),
        state=VolSelPart2SG.q6,
    ),

    # ── Q7 – Want to give tours? ──────────────────────────────────────────────
    Window(
        Const(
            "<b>Вопрос 7/7</b>\n\n"
            "Хотел(а) бы ты проводить экскурсии по кампусу для гостей?"
        ),
        Row(
            Button(Const("Да"), id="vsp2_q7_yes", on_click=on_q7_yes),
            Button(Const("Нет"), id="vsp2_q7_no", on_click=on_q7_no),
        ),
        state=VolSelPart2SG.q7,
    ),

    # ── Q7 branch – tour experience ───────────────────────────────────────────
    Window(
        Const(
            "<b>Дополнительное задание</b>\n\n"
            "Есть ли у тебя опыт в проведении экскурсий по ВШМ?"
        ),
        Row(
            Button(Const("Да"), id="vsp2_q7exp_yes", on_click=on_q7_experience_yes),
            Button(Const("Нет"), id="vsp2_q7exp_no", on_click=on_q7_experience_no),
        ),
        state=VolSelPart2SG.q7_experience,
    ),

    # ── Q7 branch – tour route ────────────────────────────────────────────────
    Window(
        Const(
            "<b>Дополнительное задание</b>\n\n"
            "Что важнее всего показать гостям в кампусе, на твой взгляд? "
            "Распиши примерный маршрут, по которому ты мог(-ла) бы провести гостей."
        ),
        TextInput(id="vsp2_q7route_input", on_success=on_q7_route_entered),
        state=VolSelPart2SG.q7_route,
    ),

    # ── Video intro ───────────────────────────────────────────────────────────
    Window(
        Const(
            "Супер! Ты ответил(а) на все письменные вопросы. Предлагаем тебе перейти к части "
            "видео-интервью. Каждый записанный кружок предполагает ограничение в 1 минуту. "
            "Постарайся уложиться в это время.\n\n"
            "<b>Внимание!</b> Не спеши отправлять кружок после записи! В телеграме можно его "
            "пересмотреть перед отправкой и удалить, если хочется перезаписать. Если его отправить, "
            "то твой ответ фиксируется.\n\n"
            "Если есть технические трудности, то пиши @zobko. Также можешь посмотреть "
            '<a href="https://docs.google.com/document/d/1xfs3T5pvM60ttPTy-fud8MtrGnq1haum6YT6yU_AOtE/edit?usp=sharing">инструкцию</a>.'
        ),
        Button(Const("Далее"), id="vsp2_video_proceed", on_click=on_video_proceed),
        state=VolSelPart2SG.video_intro,
    ),

    # ── VQ1 ───────────────────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Видео-интервью 1/3</b>\n\n"
            "Представь, что во время конференции к тебе подошёл человек, который попал сюда "
            "случайно. Представься и расскажи ему о том, что такое КБК.\n\n"
            "🎥 Запиши и отправь видео-кружок (до 1 минуты)"
        ),
        MessageInput(on_vq1, content_types=[ContentType.VIDEO_NOTE]),
        MessageInput(on_wrong_content_type, content_types=[ContentType.ANY]),
        state=VolSelPart2SG.vq1,
    ),

    # ── VQ2 ───────────────────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Видео-интервью 2/3</b>\n\n"
            "Назови две свои слабые и две сильные стороны как волонтёра.\n\n"
            "🎥 Запиши и отправь видео-кружок (до 1 минуты)"
        ),
        MessageInput(on_vq2, content_types=[ContentType.VIDEO_NOTE]),
        MessageInput(on_wrong_content_type, content_types=[ContentType.ANY]),
        state=VolSelPart2SG.vq2,
    ),

    # ── VQ3 ───────────────────────────────────────────────────────────────────
    Window(
        Const(
            "<b>Видео-интервью 3/3</b>\n\n"
            "Почему именно ты идеальный кандидат для команды КБК?\n\n"
            "🎥 Запиши и отправь видео-кружок (до 1 минуты)"
        ),
        MessageInput(on_vq3, content_types=[ContentType.VIDEO_NOTE]),
        MessageInput(on_wrong_content_type, content_types=[ContentType.ANY]),
        state=VolSelPart2SG.vq3,
    ),

    # ── Success ───────────────────────────────────────────────────────────────
    Window(
        Const(
            "🎉 <b>Ура! Поздравляем тебя с завершением тестирования.</b>\n\n"
            "Спасибо за твои старания и интерес к КБК. В скором времени мы проверим все ответы "
            "и сообщим о результатах в этом чате.\n\n"
            "Ориентировочное время: 30 марта.\n\n"
            "Следи за обновлениями в боте и подписывайся на наш основной канал: https://t.me/forumcbc\n"
            "Остались вопросы? Пиши девочкам: @savitsanastya @drkirna"
        ),
        Start(
            Const("🏠 В главное меню"),
            id="vsp2_success_home",
            state=MainMenuSG.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        state=VolSelPart2SG.success,
    ),
)
