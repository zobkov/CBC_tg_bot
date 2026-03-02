"""Aiogram Dialog definition for the creative selection part 2 (fair questionnaire)."""

from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, SwitchTo, Start
from aiogram_dialog.widgets.text import Const, Format, Multi

from .getters import get_part2_confirmation_data, get_part2_main_data
from .handlers import (
    on_q1_entered,
    on_q2_entered,
    on_q3_entered,
    on_q4_entered,
    on_q5_entered,
    on_q6_entered,
)
from .states import CreativeSelectionPart2SG
from app.bot.dialogs.guest.states import GuestMenuSG

_INTRO_TEXT = (
    "<b>Второй этап отбора на ведущего мастер-классов</b>\n\n"
    "Команда КБК'26 поздравляет тебя с успешным прохождением первого этапа отбора в творческие коллективы. "
    "Спасибо за интерес к нашему форуму и отличную работу над заявкой! \n\n"
    "Теперь тебе предстоит принять участие во <b>втором этапе</b>. Мы бы хотели узнать чуть больше о твоих "
    "идеях и навыках, и поэтому просим подробно ответить на несколько вопросов. \n\n"
    "Вопросы разделены на два блока: в первой части представлены открытые вопросы, в которых нужно будет "
    "рассказать о структуре мастер\u00a0-\u00a0класса и подходах к его проведению, а во второй — предлагается "
    "рассмотреть ситуации, которые могут возникнуть в процессе работы с аудиторией.\n\n"
    "Опираясь на твои ответы, мы сможем оценить твою готовность к решению неожиданных проблем. \n\n"
    "Желаем удачи и до встречи на форуме КБК'26!"
)

_SUCCESS_TEXT = (
    "🎉 <b>Ответы успешно отправлены!</b>\n\n"
    "Спасибо за участие во втором этапе отбора на ведущего мастер-классов. "
    "Мы рассмотрим твои ответы и свяжемся с тобой в ближайшее время.\n\n"
    "Следи за обновлениями в нашем канале и боте!"
)

_ALREADY_DONE_TEXT = (
    "<b>Второй этап отбора на ведущего мастер-классов</b>\n\n"
    "\u2705 Ты уже прошёл второй этап! Спасибо за ответы — мы свяжемся с тобой в ближайшее время.\n\n"
    "Повторное прохождение этапа недоступно."
)

creative_selection_part2_dialog = Dialog(
    # ── MAIN / intro ─────────────────────────────────────────────────────────
    Window(
        Const(_INTRO_TEXT, when="can_start"),
        Const(_ALREADY_DONE_TEXT, when="already_completed"),
        Const(
            "<b>Второй этап отбора на ведущего мастер-классов</b>\n\n"
            "⚠️ Заявка первого этапа не найдена. Обратитесь к организаторам.",
            when="no_application",
        ),
        SwitchTo(
            Const("🎭 Начать второй этап"),
            id="start_part2",
            state=CreativeSelectionPart2SG.question_1,
            when="can_start",
        ),
        Start(
            Const("⬅️ Назад"),
            id="back_to_guest",
            state=GuestMenuSG.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        state=CreativeSelectionPart2SG.MAIN,
        getter=get_part2_main_data,
    ),
    # ── Open questions (block 1) ──────────────────────────────────────────────
    Window(
        Const(
            "<b>Открытые вопросы — 1/3</b>\n\n"
            "Как ты собираешься планировать структуру мастер-класса/интерактива? "
            "Укажи основные этапы для тех активностей, которые ты выбрал."
        ),
        TextInput(id="part2_q1_input", on_success=on_q1_entered),
        state=CreativeSelectionPart2SG.question_1,
    ),
    Window(
        Const(
            "<b>Открытые вопросы — 2/3</b>\n\n"
            "Что ты будешь делать, чтобы мотивировать участников и поддерживать их интерес "
            "в процессе мастер-класса?"
        ),
        TextInput(id="part2_q2_input", on_success=on_q2_entered),
        state=CreativeSelectionPart2SG.question_2,
    ),
    Window(
        Const(
            "<b>Открытые вопросы — 3/3</b>\n\n"
            "Как ты планируешь поддерживать связь со всеми участниками во время мастер-класса "
            "(например, интересоваться, всё ли у них получается, подходить к каждому и смотреть "
            "результат, при необходимости поправлять и т.д.)?"
        ),
        TextInput(id="part2_q3_input", on_success=on_q3_entered),
        state=CreativeSelectionPart2SG.question_3,
    ),
    # ── Case questions (block 2) ──────────────────────────────────────────────
    Window(
        Const(
            "<b>Кейсы — 1/3</b>\n\n"
            "Представь ситуацию: один из участников мастер-класса отстал от остальных: пока все "
            "завершают свои изделия, он все еще в начале пути, тем не менее он не просит помощи и, "
            "возможно, выглядит растерянным или замкнутым. Что ты будешь делать в такой ситуации?"
        ),
        TextInput(id="part2_q4_input", on_success=on_q4_entered),
        state=CreativeSelectionPart2SG.question_4,
    ),
    Window(
        Const(
            "<b>Кейсы — 2/3</b>\n\n"
            "Представь ситуацию: во время мастер-класса неожиданно заканчиваются необходимые "
            "материалы (например, краски, бумага или бусины), что может вызвать замешательство "
            "и остановить процесс. Опиши свои действия в данной ситуации."
        ),
        TextInput(id="part2_q5_input", on_success=on_q5_entered),
        state=CreativeSelectionPart2SG.question_5,
    ),
    Window(
        Const(
            "<b>Кейсы — 3/3</b>\n\n"
            "К мастер-классу хочет присоединиться новый человек, хотя группа уже набрана и мест нет. "
            "Он настаивает, уверяет, что «поместится», но ты понимаешь, что это повлияет на качество "
            "и комфорт остальных. Как, на твой взгляд, следует поступить в этой ситуации?"
        ),
        TextInput(id="part2_q6_input", on_success=on_q6_entered),
        state=CreativeSelectionPart2SG.question_6,
    ),
    # ── Confirmation ──────────────────────────────────────────────────────────
    # Window(
    #     Multi(
    #         Const("✅ <b>Проверь свои ответы перед отправкой</b>\n"),
    #         Const("<b>Открытые вопросы</b>"),
    #         Format("1. {q1}"),
    #         Format("2. {q2}"),
    #         Format("3. {q3}"),
    #         Const("\n<b>Кейсы</b>"),
    #         Format("4. {q4}"),
    #         Format("5. {q5}"),
    #         Format("6. {q6}"),
    #         Const("\nВсё верно?"),
    #         sep="\n",
    #     ),
    #     Row(
    #         Button(Const("✅ Отправить"), id="submit_part2", on_click=on_submit_part2),
    #         Cancel(Const("❌ Отменить"), id="cancel_part2_confirm"),
    #     ),
    #     state=CreativeSelectionPart2SG.confirmation,
    #     getter=get_part2_confirmation_data,
    # ),
    # ── Success ───────────────────────────────────────────────────────────────
    Window(
        Const(_SUCCESS_TEXT),
        Start(Const("🏠 В главное меню"),state=GuestMenuSG.MAIN, id="go_home_part2", show_mode=StartMode.RESET_STACK),
        state=CreativeSelectionPart2SG.success,
    ),
)
