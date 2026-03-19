# volunteer selection part 2


## Testing sequence
```html
<b>Привет!</b>

Поздравляем тебя с успешным прохождением первого этапа отбора! 

Ты отлично ответил(-а) на наши вопросы, и мы предлагаем тебе пройти небольшое тестовое задание, которое поможет нам лучше понять твою мотивацию участия и узнать побольше о тебе.
```

Кнопка «Далее»

```html
<b>Важно!</b> Тестирование ограничено по времени: оно длится <b>35 минут</b>. Поэтому, когда будешь проходить его, убедись, что тебя ничего не отвлекает.

Тестирование состоит из заданий формата выбора правильного варианта ответа, развернутых ответов и небольшого интервью (тебе нужно записать кружочки в Телеграме). Интервью будет в самом конце (3 вопроса), поэтому удели достаточно времени для его прохождения.

Мы не даем строгих ограничений по времени на каждый вопрос, чтобы ты мог(-ла) спокойно выполнить все задания в рамках общего временного лимита. Поэтому ты можешь самостоятельно решить, на какие вопросы нужно уделить больше времени. 

Мы надеемся на твою искренность и добросовестность. Мы не приветствуем использование ИИ для выполнения данного задания: нам не важен идеальный ответ, сгенерированный нейросетью, а твое умение размышлять и делиться своим опытом. 

<b>Готов(-а) ли ты приступить к тестированию?</b>
``` 

Да (выводит на тестирование)
Нет (возвращает в начало)

Вопросы, требующие письменного (или кнопочного) ответа:

1)	Какой по счету КБК в этом году?
Варианты ответа (buttons):
•	1ый
•	2ой
•	3ий
•	4ый
•	5ый

2)	Когда проводится КБК в этом году? (впиши дату и месяц в формате «25 декабря»)
Короткий ответ 

3)	Какая тематика КБК в этом году?
Короткий ответ 

4)	Многие из нас имеют опыт работы в команде, и нередко у нас могут возникать разногласия с сокомандниками. 1. Опиши свой опыт работы в команде 2. Как ты обычно решаешь спорные ситуации при работе с другими людьми?
Развернутый ответ

5)	Представь, что тебе поручено встречать гостей и выдавать бейджики, и в процессе понимаешь, что не хватает бейджа для очень важного гостя. Напиши, что ты будешь делать. 
Развернутый ответ

6)	КБК – интернациональное мероприятие. Представь, что ты видишь иностранного гостя, который потерялся и что-то ищет. Опиши твои действия. 
Развернутый ответ

7)	Хотел(а) бы ты проводить экскурсии по кампусу для гостей?
•	Да (переход к доп заданию)
•	Нет (сразу переход к след. Вопросу)

Доп. задание:
Есть ли у тебя опыт в проведении экскурсий по ВШМ?
Да 
Нет

Что важнее всего показать гостям в кампусе, на твой взгляд? Распиши примерный маршрут, по которому ты мог(-ла) бы провести гостей.
Развернутый ответ

После этой части текст:

```html
Супер! Ты ответил(а) на все письменные ответы. Предлагаем тебе перейти к части видео-интервью. Каждый записанный кружок предполагает ограничение в 1 минуту. Постарайся уложиться в это время.

<b>Внимание!</b> Не спеши отправлять кружок после записи! В телеграме можно его пересмотреть перед отправкой и удалить, если хочется перезаписать. Если его отправить, то твой ответ фиксируется. 

Если есть технчиеские трудности, то пиши @zobko. Также можешь посмотреть <a href="https://docs.google.com/document/d/1xfs3T5pvM60ttPTy-fud8MtrGnq1haum6YT6yU_AOtE/edit?usp=sharing">инструкцию</a>.
```
Кнопка «Далее»

Вопросы для видео-интерьвю
1)	Представь, что во время конференции к тебе подошёл человек, который попал сюда случайно. Представься и расскажи ему о том, что такое КБК. (кружок)
2)	Назови две свои слабые и две сильные стороны как волонтёра. (кружок)
3)	Почему именно ты идеальный кандидат для команды КБК? (кружок)

После видеоинтервью вылетает текст:
```html
<b>Ура! Поздравляем тебя с завершением тестирования.</b>

Спасибо за твои старания и интерес к КБК. В скором времени мы проверим все ответы и сообщим о результатах в этом чате.

Ориентировочное время: 30 марта.

Следи за обновлениями в боте и подписывайся на наш основной канал: https://t.me/forumcbc
Остались вопросы? Пиши девочкам: @savitsanastya @drkirna 
```

### Admin checking sequence
Будет реализовано позже. Будет по команде админа /volunteer_review



## Implementation details
### DB 
Сохраняем все ответы в БД. Таблица `volunteer_selection_part2`. Нужно сделать всю инфраструктуру для этого. 

Каждый ответ сохраняется в свою ячейку. 


### Video_messages
Когда человек отправляет кружок в боту, надо сохранить file_id в БД для каждого ответа (их 3).

---

#### Пример реализации

```python
"""
Минимальный пример: приём видео-кружка, сохранение file_id, отправка другому пользователю.
Без реальной БД — хранение в памяти для демонстрации логики.
"""
# ---------------------------------------------------------------------------
# "База данных" — просто словарь в памяти
# ---------------------------------------------------------------------------

# { user_id: [file_id, file_id, ...] }
storage: dict[int, list[str]] = {}


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

class CandidateStates(StatesGroup):
    q1 = State()   # ждём первый кружок
    q2 = State()   # ждём второй кружок
    done = State() # всё записано


class AdminStates(StatesGroup):
    pick = State()   # выбираем чьи ответы смотреть
    watch = State()  # смотрим кружки


# ---------------------------------------------------------------------------
# Диалог кандидата
# ---------------------------------------------------------------------------

async def handle_q1(message: Message, widget: MessageInput, manager: DialogManager):
    # ключевой момент 1: достаём file_id из video_note
    file_id = message.video_note.file_id

    # сохраняем в dialog_data — живёт пока активен диалог
    manager.dialog_data["answers"] = [file_id]

    print(f"[Q1] user={message.from_user.id} file_id={file_id}")
    await manager.next()


async def handle_q2(message: Message, widget: MessageInput, manager: DialogManager):
    file_id = message.video_note.file_id

    # дописываем к уже сохранённым
    manager.dialog_data["answers"].append(file_id)

    # ключевой момент 2: «сохраняем в БД» — здесь просто кладём в словарь
    user_id = message.from_user.id
    storage[user_id] = manager.dialog_data["answers"]

    print(f"[Q2] user={user_id} answers={storage[user_id]}")
    await manager.next()


candidate_dialog = Dialog(
    Window(
        Const("Вопрос 1: Расскажи о себе.\nОтветь видео-кружком 🎥"),
        MessageInput(handle_q1, content_types=[ContentType.VIDEO_NOTE]),
        state=CandidateStates.q1,
    ),
    Window(
        Const("Вопрос 2: Почему хочешь к нам?\nОтветь видео-кружком 🎥"),
        MessageInput(handle_q2, content_types=[ContentType.VIDEO_NOTE]),
        state=CandidateStates.q2,
    ),
    Window(
        Const("✅ Готово! Ответы сохранены."),
        state=CandidateStates.done,
    ),
)


# ---------------------------------------------------------------------------
# Диалог админа
# ---------------------------------------------------------------------------

async def get_candidates(dialog_manager: DialogManager, **kwargs):
    # отдаём список тех, у кого есть ответы
    candidates = list(storage.keys())
    return {
        "candidates": candidates,
        "has_candidates": len(candidates) > 0,
    }


async def get_watch_data(dialog_manager: DialogManager, **kwargs):
    user_id = dialog_manager.dialog_data["target_user_id"]
    idx = dialog_manager.dialog_data.get("idx", 0)
    answers = storage.get(user_id, [])
    return {
        "user_id": user_id,
        "idx": idx + 1,
        "total": len(answers),
        "has_next": idx + 1 < len(answers),
        "has_prev": idx > 0,
    }


async def on_select_candidate(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    # для простоты берём первого из списка
    # в реальности — Select виджет передаст item_id
    user_id = list(storage.keys())[0]

    manager.dialog_data["target_user_id"] = user_id
    manager.dialog_data["idx"] = 0

    await manager.switch_to(AdminStates.watch)

    # ключевой момент 3: достаём file_id из хранилища и отправляем другому юзеру
    file_id = storage[user_id][0]
    print(f"[ADMIN] sending file_id={file_id} to admin={callback.from_user.id}")
    await callback.message.answer_video_note(file_id)  # <-- тот же file_id, другой получатель


async def on_next(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["idx"] += 1
    await _send_current(callback, manager)


async def on_prev(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["idx"] -= 1
    await _send_current(callback, manager)


async def _send_current(callback: CallbackQuery, manager: DialogManager):
    user_id = manager.dialog_data["target_user_id"]
    idx = manager.dialog_data["idx"]
    file_id = storage[user_id][idx]

    print(f"[ADMIN] sending answer #{idx} file_id={file_id}")
    await callback.message.answer_video_note(file_id)


admin_dialog = Dialog(
    Window(
        Format("Кандидаты: {candidates}\n", when="has_candidates"),
        Const("Нет ответов.", when=~F["has_candidates"]),
        Button(
            Const("▶️ Смотреть первого"),
            id="select",
            on_click=on_select_candidate,
            when="has_candidates",
        ),
        state=AdminStates.pick,
        getter=get_candidates,
    ),
    Window(
        Format("Ответ {idx}/{total} от user_id={user_id}\n⬆️ Кружок выше"),
        Button(Const("◀️"), id="prev", on_click=on_prev, when="has_prev"),
        Button(Const("▶️"), id="next", on_click=on_next, when="has_next"),
        Button(Const("↩️ Назад"), id="back",
               on_click=lambda c, b, m: m.switch_to(AdminStates.pick)),
        state=AdminStates.watch,
        getter=get_watch_data,
    ),
)

```
---