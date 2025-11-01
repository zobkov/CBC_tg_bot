
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Select, Row, Column
from aiogram_dialog.widgets.text import Const, Format, Multi
from magic_filter import F

from .getter import get_intro_data, get_question_data, get_results_data
from .handlers import (
    email_check,
    email_error_handler,
    education_check,
    education_error_handler,
    name_check,
    name_error_handler,
    on_certificate_requested,
    on_email_entered,
    on_education_entered,
    on_name_entered,
    on_phone_entered,
    on_quiz_answer_selected,
    on_quiz_restart,
    on_quiz_start,
    phone_check,
    phone_error_handler,
)
from .states import QuizDodSG


quiz_dod_dialog = Dialog(
    Window(
        Multi(
            Const(
                """大家好! Мы подготовили короткий квиз, чтобы проверить, насколько хорошо ты знаешь культуру и традиции Поднебесной, и познакомить тебя с нашим проектом.

И это только начало  👀 

Совсем скоро — лекции от экспертов, новые челленджи, онлайн-встречи с ребятами из разных регионов и другие сюрпризы от команды КБК! 

Подписывайся на наши соцсети — впереди ещё много всего интересного! 

Не тяни — жми «начать квиз» и вперёд 🚀"""
            ),
            Format(
                "<b>Твой лучший результат:</b> {best_score}/{max_questions}",
                when="has_previous_score",
            ),
            sep="\n\n",
        ),
        Column(
            Button(Const("Начать квиз"), id="quiz_dod_start", on_click=on_quiz_start),
            Cancel(Const("🏠 В личный кабинет"), id="quiz_dod_cancel_main"),
        ),
        state=QuizDodSG.MAIN,
        getter=get_intro_data,
    ),
    Window(
        Const("Напиши свою фамилию, имя и отчество полностью."),
        TextInput(
            id="Q_DOD_name",
            on_error=name_error_handler,
            on_success=on_name_entered,
            type_factory=name_check,
        ),
        state=QuizDodSG.name,
    ),
    Window(
        Const("Напиши номер телефона в формате <b>+7XXXXXXXXXX</b>."),
        TextInput(
            id="Q_DOD_phone",
            on_error=phone_error_handler,
            on_success=on_phone_entered,
            type_factory=phone_check,
        ),
        state=QuizDodSG.phone,
    ),
    Window(
        Const("Укажи действующий e-mail. Не волнуйся, мы не отправляем спам."),
        TextInput(
            id="Q_DOD_email",
            on_error=email_error_handler,
            on_success=on_email_entered,
            type_factory=email_check,
        ),
        state=QuizDodSG.email,
    ),
    Window(
        Const("Укажи школу / университет, класс / курс.\n\nНапример: <b>ГБОУ СОШ №241, 11 класс</b>  /  <b>ВШМ СПбГУ, 1 курс, Международный Менеджмент.</b>"),
        TextInput(
            id="Q_DOD_education",
            on_error=education_error_handler,
            on_success=on_education_entered,
            type_factory=education_check,   
        ),
        state=QuizDodSG.education,
    ),
    Window(
        Multi(
            Const("<b>Квиз КБК</b>"),
            Format("<b>{current_question}/{max_questions}</b>"),
            Format("❓ <i>{question_text}</i>\n"),
            Format("{answer_options}"),
            sep="\n\n",
        ),
        Group(
            Select(
                Format("{item[text]}"),
                id="quiz_dod_option",
                items="options",
                item_id_getter=lambda item: item["id"],
                on_click=on_quiz_answer_selected,
            ),
            width=1,
        ),
        state=QuizDodSG.QUESTIONS,
        getter=get_question_data,
    ),
    Window(
        Multi(
            Format(
                """<b>{correct_answers}/{max_questions}</b> – «Настоящий эксперт КБК»

Поздравляем, {name}!
               
Ты знаешь Китай и КБК так, будто уже в команде организаторов.
С таким багажом знаний можно смело лететь в Шанхай и проводить деловые переговоры!

Твой заслуженный стикерпак уже ждёт на стенде!""",
                when="passed_threshold",
            ),
            Format(
                """<b>{correct_answers}/{max_questions}</b> – «Ученик КБК»

Хорошее начало, {name}!
               
Теперь ты знаешь больше о форуме, традициях Китая и возможностях ВШМ СПбГУ.

Попробуй пройти квиз ещё раз, и помни, что путь к успеху начинается с интереса, а он у тебя уже есть!""",
                when=~F["passed_threshold"],
            ),
            Format("🎯 Новый личный рекорд!", when="best_updated"),
            Format(
                "<b>Лучший результат:</b> {best_score}/{max_questions}",
                when="has_previous_score",
            ),
            sep="\n\n",
        ),
        Column(
            Button(
                Const("Перепройти квиз"),
                id="quiz_dod_restart",
                on_click=on_quiz_restart,
            ),
            Button(
                Const("Получить сертификат"),
                id="quiz_dod_get_certificate",
                on_click=on_certificate_requested,
                when="can_request_certificate",
            ),
            Cancel(Const("🏠 В личный кабинет"), id="quiz_dod_cancel_results"),
        ),
        state=QuizDodSG.RESULTS,
        getter=get_results_data,
    ),
)