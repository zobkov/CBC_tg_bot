#!/usr/bin/env python3
"""
Broadcast script — Volunteer selection: Photographers, PASSED.

Sends congratulations + confirmation buttons (Yes / No) to photographers
listed in the CSV. Upon clicking, the bot notifies 721299210 and 257026813.

Modes:
  1. TEST  — send only to ADMIN_USER_ID (257026813)
  2. LIVE  — send to all user_ids from the CSV
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
SOURCE_CSV = "КБК 26 Отбор волонтеров - фотографы_прошли.csv"

_MESSAGE_TEXT = (
    "<b>Привет!</b>\n\n"
    "Поздравляем тебя с успешным прохождением отбора на роль фотографа/видеографа "
    "на форуме КБК!\n\n\n"
    "<b>Пожалуйста, подтверди свое участие до конца пятницы (20.03 23.59)</b>"
)

# ── Logging ───────────────────────────────────────────────────────────────────


def setup_logging() -> logging.Logger:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("storage").mkdir(exist_ok=True)
    logger = logging.getLogger("vol_photographers_passed_broadcast")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    fh = logging.FileHandler(
        f"storage/vol_photographers_passed_broadcast_{timestamp}.log", encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


# ── Helpers ───────────────────────────────────────────────────────────────────


def load_user_ids() -> list[int]:
    path = Path(SOURCE_CSV)
    if not path.exists():
        raise FileNotFoundError(f"{SOURCE_CSV} not found")
    ids = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0].strip().isdigit():
                ids.append(int(row[0].strip()))
    return ids


def create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="vol_photo_confirm_yes"),
                InlineKeyboardButton(
                    text="К сожалению, нет", callback_data="vol_photo_confirm_no"
                ),
            ]
        ]
    )


def preview(logger: logging.Logger) -> None:
    logger.info("=" * 60)
    logger.info("MESSAGE PREVIEW")
    logger.info("=" * 60)
    print("\n📝 Message text:")
    print(_MESSAGE_TEXT)
    print("\n🔘 Buttons:")
    print("   [Да]  (callback: vol_photo_confirm_yes)")
    print("   [К сожалению, нет]  (callback: vol_photo_confirm_no)")
    print("\nℹ️  Responses will be forwarded to: 721299210, 257026813")
    print("=" * 60 + "\n")


def select_mode(logger: logging.Logger) -> str:
    print("\n" + "=" * 60)
    print("BROADCAST MODE")
    print("=" * 60)
    print(f"1. 🧪 TEST  — send only to admin ({ADMIN_USER_ID})")
    print(f"2. 🚀 LIVE  — send to all users in CSV")
    print("=" * 60)
    while True:
        choice = input("\nSelect mode (1/2): ").strip()
        if choice == "1":
            logger.info("Mode: TEST")
            return "test"
        if choice == "2":
            confirm = input("⚠️  Send to ALL users in CSV? (yes/no): ").strip().lower()
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
                logger.info(
                    "Progress: %d/%d sent=%d blocked=%d errors=%d",
                    idx, stats["total"], stats["sent"], stats["blocked"], stats["errors"],
                )
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
                await bot.send_message(
                    chat_id=user_id,
                    text=_MESSAGE_TEXT,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
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
    logger.info("VOL PHOTOGRAPHERS PASSED BROADCAST")
    logger.info("=" * 60)

    config = load_config()
    bot = Bot(token=config.tg_bot.token)

    try:
        all_ids = load_user_ids()
        logger.info("Loaded %d user IDs from '%s'", len(all_ids), SOURCE_CSV)

        preview(logger)
        mode = select_mode(logger)

        user_ids = [ADMIN_USER_ID] if mode == "test" else all_ids

        logger.info("Sending to %d users...", len(user_ids))
        stats = await send_broadcast(bot, user_ids, logger)

        logger.info("=" * 60)
        logger.info("DONE  total=%d sent=%d blocked=%d errors=%d",
                    stats["total"], stats["sent"], stats["blocked"], stats["errors"])
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Cancelled by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
