"""
Диалог квиза на день открытых дверей
"""
from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import Row, Back, Start, SwitchTo, Next, Select
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia
from aiogram_dialog.widgets.input import TextInput

# from .getters import *
from .states import QuizDodSG
from .handlers import (
    name_error_handler,
    email_error_handler,
    phone_error_handler,
    name_check,
    email_check,
    phone_check
)



quiz_dod_dialog = Dialog(
    # Главное меню квиза
    Window(
        Const("""大家好! Мы подготовили короткий квиз, чтобы проверить, насколько хорошо ты знаешь культуру и традиции Поднебесной, и познакомить тебя с нашим проектом.

И это только начало  👀 

Совсем скоро — лекции от экспертов, новые челленджи, онлайн-встречи с ребятами из разных регионов и другие сюрпризы от команды КБК! 

Подписывайся на наши соцсети — впереди ещё много всего интересного! 

Не тяни — жми «начать квиз» и вперёд 🚀"""),
        SwitchTo(Const("Начать квиз"), QuizDodSG.name),
        state=QuizDodSG.MAIN,
    ),

    # Начальная анкета

    # name
    Window(
        Const("Введи своё имя и фамилию:"),
        TextInput(
            id="Q_DOD_name",
            on_error=name_error_handler,
            on_success=Next(),
            type_factory=name_check,
        ),
        state=QuizDodSG.name
    ),
    # telephone
    Window(
        Const("Введи свой номер телефона:"),
        TextInput(
            id="Q_DOD_phone",
            on_error=phone_error_handler,
            on_success=Next(),
            type_factory=phone_check,
        ),
        state=QuizDodSG.phone
    ),
    # e-mail
    Window(
        Const("Введи свою электронную почту:"),
        TextInput(
            id="Q_DOD_email",
            on_error=email_error_handler,
            on_success=Next(show_mode=ShowMode.DELETE_AND_SEND),
            type_factory=email_check,
        ),
        state=QuizDodSG.email
    ),

    Window(
        Const("<b>Квиз от КБК</b>\n\n\n"),
        Format("""<b>{current_question}/{max_questions}</b>
               
❓ <i>{question_text}</i>"""), # question TODO
        Select(),
        #getter=,
        state=QuizDodSG.QUESTIONS
    ),

    Window(
        Format("""<b>{correct_answers}/{max_questions}</b> – «Настоящий эксперт КБК»

Поздравляем, {name}!
               
Ты знаешь Китай и КБК так, будто уже в команде организаторов.
С таким багажом знаний можно смело лететь в Шанхай и проводить деловые переговоры!

Твой заслуженный стикерпак уже ждёт на стенде!""", when=passed_threshold),
        Format("""<b>{correct_answers}/{max_questions}</b> – «Ученик КБК»

Хорошее начало, {name}!
               
Теперь ты знаешь больше о форуме, традициях Китая и возможностях ВШМ СПбГУ.

Попробуй пройти квиз ещё раз, и помни, что путь к успеху начинается с интереса, а он у тебя уже есть!""", when=not_passed_threshold),
        SwitchTo(Const("Перепройти квиз"),QuizDodSG.QUESTIONS),
        state=QuizDodSG.RESULTS,
    ),


)