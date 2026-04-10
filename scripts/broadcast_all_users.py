#!/usr/bin/env python3
"""
Broadcast a message to ALL users in the users table.

Fetches every non-blocked user_id directly from the database and sends
the hardcoded MESSAGE via the bot.

Usage (run from the project root):
    python3 scripts/broadcast_all_users.py

Modes (interactive):
    1. TEST — send only to ADMIN_USER_ID
    2. LIVE — send to every user in the users table
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.database.models.users import Users
from app.infrastructure.database.sqlalchemy_core import session_scope
from config.config import load_config

# ============================================================================
# EDIT YOUR MESSAGE HERE
# ============================================================================

MESSAGE = """Уже завтра! 🔥

Друзья, КБК стартует меньше, чем через день. Напоминаем: регистрация обязательна для входа на форум! 

⏰11 апреля в 10:00.
📍Михайловская Дача (Санкт-Петербургское шоссе, 109)

Что нужно сделать прямо сейчас:
➡️ Зарегистрироваться по ссылке, если ещё не успели: https://forum-cbc.ru/
➡️ Зарядиться хорошим настроением :)

Если вы уже зарегистрированы, просто готовьтесь. Если нет — не тяните! 

Ждём вас!"""

# ============================================================================
# END OF MESSAGE
# ============================================================================

ADMIN_USER_ID = 257026813
DELAY_BETWEEN_MESSAGES = 0.05  # seconds — keeps well within Telegram rate limits


# ── Logging ──────────────────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("storage").mkdir(exist_ok=True)
    logger = logging.getLogger("broadcast_all_users")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    fh = logging.FileHandler(
        f"storage/broadcast_all_users_{timestamp}.log", encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


# ── Database ─────────────────────────────────────────────────────────────────

async def fetch_all_user_ids() -> list[int]:
    """Return all non-blocked user_ids from the users table."""
    async with session_scope() as session:
        stmt = (
            select(Users.user_id)
            .where(Users.is_blocked.is_(False))
            .order_by(Users.user_id)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]


# ── Interactive ───────────────────────────────────────────────────────────────

def preview(logger: logging.Logger) -> None:
    logger.info("=" * 60)
    logger.info("MESSAGE PREVIEW")
    logger.info("=" * 60)
    print("\n📝 Message text:\n")
    print(MESSAGE)
    print("\n" + "=" * 60 + "\n")


def select_mode(logger: logging.Logger) -> str:
    print("\n" + "=" * 60)
    print("BROADCAST MODE")
    print("=" * 60)
    print(f"1. 🧪 TEST  — send only to admin ({ADMIN_USER_ID})")
    print("2. 🚀 LIVE  — send to ALL users in the users table")
    print("=" * 60)
    while True:
        choice = input("\nSelect mode (1/2): ").strip()
        if choice == "1":
            logger.info("Mode: TEST")
            return "test"
        if choice == "2":
            confirm = input("⚠️  Send to ALL users in the database? (yes/no): ").strip().lower()
            if confirm == "yes":
                logger.info("Mode: LIVE")
                return "live"
            print("Cancelled.")
        else:
            print("Enter 1 or 2.")


# ── Send ──────────────────────────────────────────────────────────────────────

async def send_broadcast(
    bot: Bot,
    user_ids: list[int],
    logger: logging.Logger,
) -> None:
    stats = {"total": len(user_ids), "sent": 0, "blocked": 0, "errors": 0}

    for idx, user_id in enumerate(user_ids, 1):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=MESSAGE,
                parse_mode="HTML",
            )
            stats["sent"] += 1
            if idx % 50 == 0 or idx == stats["total"]:
                logger.info(
                    "Progress: %d/%d  sent=%d  blocked=%d  errors=%d",
                    idx, stats["total"], stats["sent"], stats["blocked"], stats["errors"],
                )
            await asyncio.sleep(DELAY_BETWEEN_MESSAGES)

        except TelegramRetryAfter as e:
            logger.warning("Rate limited — sleeping %ds", e.retry_after)
            await asyncio.sleep(e.retry_after)
            # retry once
            try:
                await bot.send_message(chat_id=user_id, text=MESSAGE, parse_mode="HTML")
                stats["sent"] += 1
            except Exception as retry_exc:
                logger.error("Retry failed for %d: %s", user_id, retry_exc)
                stats["errors"] += 1

        except TelegramForbiddenError:
            logger.warning("User %d blocked the bot", user_id)
            stats["blocked"] += 1

        except TelegramBadRequest as e:
            logger.warning("Bad request for user %d: %s", user_id, e)
            stats["blocked"] += 1

        except Exception as e:
            logger.error("Unexpected error for user %d: %s", user_id, e)
            stats["errors"] += 1

    logger.info(
        "Broadcast complete. total=%d  sent=%d  blocked=%d  errors=%d",
        stats["total"], stats["sent"], stats["blocked"], stats["errors"],
    )


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    logger = setup_logging()

    preview(logger)
    mode = select_mode(logger)

    config = load_config()
    bot = Bot(token=config.tg_bot.token)

    try:
        if mode == "test":
            user_ids = [ADMIN_USER_ID]
            logger.info("TEST mode: sending to %d", ADMIN_USER_ID)
        else:
            logger.info("Fetching user IDs from database…")
            user_ids = await fetch_all_user_ids()
            logger.info("Found %d users", len(user_ids))
            if not user_ids:
                logger.warning("No users found — aborting.")
                return

        await send_broadcast(bot, user_ids, logger)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
