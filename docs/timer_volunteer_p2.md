# Timer

Таймер запускается, когда пользователь начинает тестирование. Создается 3 задачи:
  • T+35min → "Осталось 10 минут"
  • T+40min → "Осталось 5 минут"  
  • T+45min → авто-завершение теста (force_finish)

Пользователю отправляетс сообщение, что тест запущен. Время начала (МСК)




# ПРИМЕР РЕАЛИЗАЦИИ
## Архитектура: APScheduler + RedisJobStore

Это оптимальное решение для твоего стека — персистентные задачи без Celery, восстанавливаются после перезапуска бота.

---

### Схема работы

```
Пользователь начинает тест
         │
         ▼
PostgreSQL: сохраняем started_at, deadline, status='active'
         │
         ▼
APScheduler планирует 3 задачи в Redis:
  • T+35min → "Осталось 10 минут"
  • T+40min → "Осталось 5 минут"  
  • T+45min → авто-завершение теста (force_finish)
         │
         ▼
Bot restart → APScheduler читает Redis → задачи живы ✅
```

---

### Ключевые части реализации

**1. Инициализация APScheduler с RedisJobStore**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

jobstores = {
    "default": RedisJobStore(
        jobs_key="apscheduler_jobs",
        run_times_key="apscheduler_run_times",
        host="localhost",
        port=6379,
        db=1,  # отдельная БД от основного Redis
    )
}

scheduler = AsyncIOScheduler(jobstores=jobstores)
scheduler.start()
```

**2. Запуск теста и планирование уведомлений**

```python
from datetime import datetime, timedelta

TEST_DURATION = timedelta(minutes=45)

async def start_test(user_id: int, bot: Bot, session: AsyncSession):
    started_at = datetime.utcnow()
    deadline = started_at + TEST_DURATION

    # Сохраняем в PostgreSQL
    await save_test_session(session, user_id, started_at, deadline)

    # Уникальные job_id — защита от дублей при повторном запуске
    scheduler.add_job(
        send_reminder,
        trigger="date",
        run_date=deadline - timedelta(minutes=10),
        args=[user_id, bot, "⏰ Осталось 10 минут!"],
        id=f"reminder_10_{user_id}",
        replace_existing=True,  # важно!
        misfire_grace_time=60,  # выполнить, если бот был недоступен до 60с
    )
    scheduler.add_job(
        send_reminder,
        trigger="date",
        run_date=deadline - timedelta(minutes=5),
        args=[user_id, bot, "🔴 Осталось 5 минут!"],
        id=f"reminder_5_{user_id}",
        replace_existing=True,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        force_finish_test,
        trigger="date",
        run_date=deadline,
        args=[user_id, bot, session],
        id=f"finish_{user_id}",
        replace_existing=True,
        misfire_grace_time=300,  # до 5 минут grace для финального завершения
    )

    await bot.send_message(
        user_id,
        f"🚀 Тест начат в {started_at.strftime('%H:%M')} UTC\n"
        f"⏳ Дедлайн: {deadline.strftime('%H:%M')} UTC\n"
        f"Время на выполнение: 45 минут."
    )
```

**3. Обработчики уведомлений**

```python
async def send_reminder(user_id: int, bot: Bot, text: str):
    # Проверяем — вдруг пользователь уже завершил тест досрочно
    async with async_session() as session:
        test = await get_active_test(session, user_id)
        if test and test.status == "active":
            await bot.send_message(user_id, text)

async def force_finish_test(user_id: int, bot: Bot):
    async with async_session() as session:
        test = await get_active_test(session, user_id)
        if not test or test.status != "active":
            return  # уже завершён вручную

        # Фиксируем принудительное завершение
        await mark_test_finished(session, user_id, reason="timeout")

        await bot.send_message(
            user_id,
            "⛔ Время вышло! Тест завершён автоматически."
        )
        # Сбрасываем диалог aiogram-dialog
        # Нужен доступ к storage через dp
        await reset_dialog_state(user_id, bot)
```

**4. Очистка задач при досрочном завершении**

```python
def cancel_test_jobs(user_id: int):
    for job_id in [f"reminder_10_{user_id}", f"reminder_5_{user_id}", f"finish_{user_id}"]:
        job = scheduler.get_job(job_id)
        if job:
            job.remove()
```

**5. Важный момент: сброс диалога из внешнего контекста**

```python
# В aiogram-dialog нет прямого способа сбросить диалог извне.
# Решение — через FSMContext напрямую:

from aiogram.fsm.storage.redis import RedisStorage

async def reset_dialog_state(user_id: int, bot: Bot, storage: RedisStorage):
    state = FSMContext(storage=storage, key=StorageKey(
        bot_id=bot.id,
        chat_id=user_id,
        user_id=user_id,
    ))
    await state.clear()
    await bot.send_message(user_id, "Диалог сброшен.")
```

---

### Защита от edge cases

```python
# При каждом ответе на вопрос — проверять дедлайн
async def answer_question_handler(callback: CallbackQuery, ...):
    test = await get_active_test(session, user_id)
    
    if datetime.utcnow() > test.deadline:
        # Гонка: таймер ещё не сработал, но время уже вышло
        await force_finish_test(user_id, bot)
        return
    
    # продолжаем обработку ответа...
```

---

### Итоговая надёжность

- **Перезапуск бота** → APScheduler восстанавливает все 3 задачи из Redis ✅  
- **Misfire** (бот лежал) → `misfire_grace_time` решает ✅  
- **Досрочное завершение** → `cancel_test_jobs()` убирает задачи из Redis ✅  
- **Дублирование** → `replace_existing=True` + уникальные `job_id` ✅  
- **Гонка состояний** → double-check статуса в БД перед каждым действием ✅