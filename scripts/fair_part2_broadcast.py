#!/usr/bin/env python3
"""
Broadcast script for creative selection PART 2 — Fair (Ярмарка культуры).

Sends the success message with a "🎭 Начать второй этап" button to users
listed in export_fair.csv.

Modes:
  1. TEST  — send only to ADMIN_USER_ID (257026813)
  2. LIVE  — send to all user_ids from export_fair.csv
"""

import asyncio
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import load_config

# ── Config ────────────────────────────────────────────────────────────────────

ADMIN_USER_ID = 257026813
FAIR_CSV = "export_fair.csv"

_MESSAGE_TEXT = (
    "<b>Второй этап отбора на ведущего мастер-классов</b>\n\n"
    "Команда КБК'26 поздравляет тебя с успешным прохождением первого этапа отбора в творческие "
    "коллективы. Спасибо за интерес к нашему форуму и отличную работу над заявкой! \n\n"
    "Теперь тебе предстоит принять участие во <b>втором этапе</b>. Мы бы хотели узнать чуть "
    "больше о твоих идеях и навыках, и поэтому просим подробно ответить на несколько вопросов. \n\n"
    "Вопросы разделены на два блока: в первой части представлены открытые вопросы, в которых "
    "нужно будет рассказать о структуре мастер\u00a0-\u00a0класса и подходах к его проведению, "
    "а во второй — предлагается рассмотреть ситуации, которые могут возникнуть в процессе работы "
    "с аудиторией.\n\n"
    "Опираясь на твои ответы, мы сможем оценить твою готовность к решению неожиданных проблем. \n\n"
    "Желаем удачи и до встречи на форуме КБК'26!"
)

# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("storage").mkdir(exist_ok=True)
    logger = logging.getLogger("fair_part2_broadcast")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    fh = logging.FileHandler(f"storage/fair_part2_broadcast_{timestamp}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_fair_user_ids() -> list[int]:
    """Read user_ids from export_fair.csv (one id per line, no header)."""
    path = Path(FAIR_CSV)
    if not path.exists():
        raise FileNotFoundError(f"{FAIR_CSV} not found")
    ids = []
    with path.open(newline="") as f:
        for row in csv.reader(f):
            if row and row[0].strip().isdigit():
                ids.append(int(row[0].strip()))
    return ids


def create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🎭 Начать второй этап",
            callback_data="start_creative_selection_part2",
        )
    ]])


def preview(logger: logging.Logger) -> None:
    logger.info("=" * 60)
    logger.info("MESSAGE PREVIEW")
    logger.info("=" * 60)
    print("\n📝 Message text:")
    print(_MESSAGE_TEXT)
    print("\n🔘 Button: 🎭 Начать второй этап")
    print("   └─ callback_data: start_creative_selection_part2")
    print("=" * 60 + "\n")


def select_mode(logger: logging.Logger) -> str:
    print("\n" + "=" * 60)
    print("BROADCAST MODE")
    print("=" * 60)
    print(f"1. 🧪 TEST  — send only to admin ({ADMIN_USER_ID})")
    print(f"2. 🚀 LIVE  — send to all {FAIR_CSV} users")
    print("=" * 60)
    while True:
        choice = input("\nSelect mode (1/2): ").strip()
        if choice == "1":
            logger.info("Mode: TEST")
            return "test"
        if choice == "2":
            confirm = input(f"⚠️  Send to ALL users in {FAIR_CSV}? (yes/no): ").strip().lower()
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
) -> dict:
    keyboard = create_keyboard()
    stats = {"total": len(user_ids), "sent": 0, "blocked": 0, "errors": 0}

    for idx, user_id in enumerate(user_ids, 1):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=_MESSAGE_TEXT,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            stats["sent"] += 1
            if idx % 10 == 0:
                logger.info("Progress: %d/%d sent=%d blocked=%d errors=%d",
                            idx, stats["total"], stats["sent"], stats["blocked"], stats["errors"])
            await asyncio.sleep(0.4)

        except TelegramForbiddenError:
            logger.warning("User %d blocked bot", user_id)
            stats["blocked"] += 1

        except TelegramBadRequest as e:
            logger.warning("Bad request for user %d: %s", user_id, e)
            if any(k in str(e).lower() for k in ("chat not found", "user not found", "blocked")):
                stats["blocked"] += 1
            else:
                stats["errors"] += 1

        except TelegramRetryAfter as e:
            logger.warning("Rate limit — sleeping %ds", e.retry_after)
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(chat_id=user_id, text=_MESSAGE_TEXT,
                                       reply_markup=keyboard, parse_mode="HTML")
                stats["sent"] += 1
            except Exception as retry_err:
                logger.error("Retry failed for %d: %s", user_id, retry_err)
                stats["errors"] += 1

        except Exception as e:
            logger.error("Unexpected error for user %d: %s", user_id, e)
            stats["errors"] += 1

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("FAIR PART 2 BROADCAST SCRIPT")
    logger.info("=" * 60)

    config = load_config()
    bot = Bot(token=config.tg_bot.token)

    try:
        all_fair_ids = load_fair_user_ids()
        logger.info("Loaded %d user IDs from %s", len(all_fair_ids), FAIR_CSV)

        preview(logger)
        mode = select_mode(logger)

        if mode == "test":
            user_ids = [ADMIN_USER_ID]
        else:
            user_ids = all_fair_ids

        logger.info("Sending to %d users...", len(user_ids))
        stats = await send_broadcast(bot, user_ids, logger)

        logger.info("=" * 60)
        logger.info("DONE")
        logger.info("Total: %d  Sent: %d  Blocked: %d  Errors: %d",
                    stats["total"], stats["sent"], stats["blocked"], stats["errors"])
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Cancelled by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
