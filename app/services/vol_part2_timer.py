"""APScheduler-based timer service for volunteer selection part 2.

Timer flow (per user):
  T+0   -> test starts (on_start_yes handler)
  T+35m -> reminder: 10 minutes left
  T+40m -> reminder: 5 minutes left
  T+45m -> force_finish (notify + clear FSM state)

Jobs are stored in Redis (db=2) for persistence across bot restarts.
Falls back to in-memory store if RedisJobStore is unavailable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_timer_scheduler: AsyncIOScheduler | None = None

# ── Timer durations (change these for testing) ───────────────────────────────
TEST_DURATION_MIN = 3       # total test length in minutes
REMINDER_1_OFFSET_MIN = 1   # T+ minutes → "10 минут осталось"
REMINDER_2_OFFSET_MIN = 2   # T+ minutes → "5 минут осталось"
FINISH_OFFSET_MIN = 3       # T+ minutes → force_finish
# ─────────────────────────────────────────────────────────────────────────────

MSK_OFFSET = timedelta(hours=3)

STARTED_TEXT = (
    "<b>Тест начат!</b>\n\n"
    "Старт: <b>{started}</b> МСК\n"
    "Дедлайн: <b>{deadline}</b> МСК\n\n"
    f"Время на выполнение: {TEST_DURATION_MIN} минут."
)
_REMINDER_10_TEXT = (
    "<b>Осталось 10 минут!</b>\n\n"
    "Поторопись завершить тестирование."
)
_REMINDER_5_TEXT = (
    "<b>Осталось 5 минут!</b>\n\n"
    "Постарайся завершить оставшиеся вопросы."
)
_TIMEOUT_TEXT = (
    "<b>Время вышло!</b>\n\n"
    "Тестирование завершено автоматически. Если не успел(а) ответить на все вопросы, "
    "обратись к организаторам: @savitsanastya @drkirna"
)


def init_timer_scheduler(
    redis_host: str,
    redis_port: int,
    redis_password: str | None = None,
) -> AsyncIOScheduler:
    """Initialize the timer scheduler with RedisJobStore (falls back to in-memory)."""
    global _timer_scheduler  # noqa: PLW0603

    try:
        from apscheduler.jobstores.redis import RedisJobStore

        redis_kwargs: dict = {"host": redis_host, "port": redis_port, "db": 2}
        if redis_password:
            redis_kwargs["password"] = redis_password

        jobstores = {
            "timers": RedisJobStore(
                jobs_key="vol2_timer_jobs",
                run_times_key="vol2_timer_run_times",
                **redis_kwargs,
            )
        }
        _timer_scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone="Europe/Moscow",
        )
        logger.info("\u2705 Vol2 timer scheduler init with RedisJobStore (db=2)")
    except Exception as exc:
        logger.warning(
            "[VOL2_TIMER] RedisJobStore unavailable (%s); using in-memory scheduler"
            " (timers won't survive restarts)",
            exc,
        )
        from apscheduler.jobstores.memory import MemoryJobStore

        _timer_scheduler = AsyncIOScheduler(
            jobstores={"timers": MemoryJobStore()},
            timezone="Europe/Moscow",
        )

    return _timer_scheduler


def get_timer_scheduler() -> AsyncIOScheduler | None:
    """Return the active timer scheduler instance."""
    return _timer_scheduler


def schedule_user_timer(user_id: int) -> None:
    """Schedule 3 timed jobs for a user's test session."""
    scheduler = _timer_scheduler
    if scheduler is None or not scheduler.running:
        logger.warning(
            "[VOL2_TIMER] Scheduler not running; timer not scheduled for user_id=%d",
            user_id,
        )
        return

    now = datetime.now(tz=timezone.utc)
    scheduler.add_job(
        _send_reminder_job,
        trigger="date",
        run_date=now + timedelta(minutes=REMINDER_1_OFFSET_MIN),
        args=[user_id, _REMINDER_10_TEXT],
        id=f"vol2_r10_{user_id}",
        jobstore="timers",
        replace_existing=True,
        misfire_grace_time=120,
    )
    scheduler.add_job(
        _send_reminder_job,
        trigger="date",
        run_date=now + timedelta(minutes=REMINDER_2_OFFSET_MIN),
        args=[user_id, _REMINDER_5_TEXT],
        id=f"vol2_r5_{user_id}",
        jobstore="timers",
        replace_existing=True,
        misfire_grace_time=120,
    )
    scheduler.add_job(
        _force_finish_job,
        trigger="date",
        run_date=now + timedelta(minutes=FINISH_OFFSET_MIN),
        args=[user_id],
        id=f"vol2_finish_{user_id}",
        jobstore="timers",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("[VOL2_TIMER] Timer scheduled for user_id=%d (deadline in 45 min)", user_id)


def cancel_user_timer(user_id: int) -> None:
    """Remove all pending timer jobs for a user (call when test is completed)."""
    scheduler = _timer_scheduler
    if scheduler is None:
        return
    for job_id in (
        f"vol2_r10_{user_id}",
        f"vol2_r5_{user_id}",
        f"vol2_finish_{user_id}",
    ):
        try:
            job = scheduler.get_job(job_id, jobstore="timers")
            if job:
                job.remove()
                logger.info("[VOL2_TIMER] Cancelled job %s", job_id)
        except Exception as exc:
            logger.warning("[VOL2_TIMER] Could not cancel job %s: %s", job_id, exc)


# Job functions must be at module level for APScheduler pickle serialisation

async def _send_reminder_job(user_id: int, text: str) -> None:
    """Send a timed reminder if the user has not finished the test yet."""
    from app.services.app_container import get_container
    from app.infrastructure.database.sqlalchemy_core import get_session_factory
    from app.infrastructure.database.database.db import DB

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            db = DB(session)
            app = await db.volunteer_selection_part2.get(user_id=user_id)
            if app and app.vq1_file_id and app.vq2_file_id and app.vq3_file_id:
                logger.info(
                    "[VOL2_TIMER] user_id=%d already completed; skipping reminder", user_id
                )
                return
    except Exception as exc:
        logger.error(
            "[VOL2_TIMER] DB check failed in reminder for user_id=%d: %s", user_id, exc
        )

    try:
        bot = get_container().bot
        await bot.send_message(user_id, text, parse_mode="HTML")
        logger.info("[VOL2_TIMER] Reminder sent to user_id=%d", user_id)
    except Exception as exc:
        logger.error("[VOL2_TIMER] Send reminder failed for user_id=%d: %s", user_id, exc)


async def _force_finish_job(user_id: int) -> None:
    """Force-finish the test: clear FSM state and notify the user."""
    from app.services.app_container import get_container
    from app.infrastructure.database.sqlalchemy_core import get_session_factory
    from app.infrastructure.database.database.db import DB

    # 1. Skip if already completed
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            db = DB(session)
            app = await db.volunteer_selection_part2.get(user_id=user_id)
            if app and app.vq1_file_id and app.vq2_file_id and app.vq3_file_id:
                logger.info(
                    "[VOL2_TIMER] user_id=%d already completed; skipping force_finish", user_id
                )
                return
    except Exception as exc:
        logger.error(
            "[VOL2_TIMER] DB check failed in force_finish for user_id=%d: %s", user_id, exc
        )

    # 2. Clear FSM / dialog state via direct Redis key deletion.
    #    aiogram-dialog scatters state across multiple Redis keys with pattern
    #    fsm:{bot_id}:{chat_id}:{user_id}:* (stack, context entries, etc.).
    #    state.clear() on a single StorageKey only removes one destiny's data,
    #    so we must scan and delete every matching key explicitly.
    c = get_container()
    try:
        redis = c.dp.storage.redis
        pattern = f"fsm:{c.bot.id}:{user_id}:{user_id}:*"
        keys = [key async for key in redis.scan_iter(pattern)]
        if keys:
            await redis.delete(*keys)
            logger.info(
                "[VOL2_TIMER] Deleted %d FSM keys for user_id=%d (pattern=%s)",
                len(keys), user_id, pattern,
            )
        else:
            logger.info("[VOL2_TIMER] No FSM keys found for user_id=%d", user_id)
    except Exception as exc:
        logger.error("[VOL2_TIMER] FSM clear failed for user_id=%d: %s", user_id, exc)

    # 3. Notify user
    try:
        await c.bot.send_message(user_id, _TIMEOUT_TEXT, parse_mode="HTML")
        logger.info("[VOL2_TIMER] Force-finish message sent to user_id=%d", user_id)
    except Exception as exc:
        logger.error("[VOL2_TIMER] Notify failed for user_id=%d: %s", user_id, exc)
