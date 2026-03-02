#!/usr/bin/env python3
"""
Send a message to one or several users by their Telegram user_id.

Usage:
    python3 scripts/send_message.py <user_id> [<user_id> ...]

Example:
    python3 scripts/send_message.py 123456789 987654321

The message is hardcoded in the MESSAGE constant below.
BOT_TOKEN is read from the .env file in the project root.
"""

import asyncio
import sys
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from dotenv import load_dotenv
import os

# ============================================================================
# EDIT YOUR MESSAGE HERE
# ============================================================================

MESSAGE = """Привет! Спасибо тебе за заявку, в ней чувствуется искренний интерес. Но у нас было очень много сильных кандидатов, и на одно место претендовало действительно большое количество людей. В итоге выбор сместился в сторону тех, у кого был либо прямой опыт проведения мастер-классов из списка, либо глубокое погружение в китайскую культуру. Это не значит, что твой опыт хуже или недостаточен, просто в этот раз конкурс сформировался под конкретную задачу. Мы будем рады, если ты останешься с нами на связи. У КБК'26 есть и другие форматы, где расстояние не будет помехой, и мы будем рады видеть тебя среди участников."""

# ============================================================================
# END OF MESSAGE
# ============================================================================


def load_token() -> str:
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERROR: BOT_TOKEN not found in .env file.")
        sys.exit(1)
    return token


async def send_to_users(bot: Bot, user_ids: list[int]) -> None:
    ok, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=MESSAGE, parse_mode="HTML")
            print(f"  [OK]   {uid}")
            ok += 1
        except TelegramForbiddenError:
            print(f"  [SKIP] {uid} — bot is blocked by user")
            failed += 1
        except TelegramBadRequest as e:
            print(f"  [FAIL] {uid} — bad request: {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] {uid} — unexpected error: {e}")
            failed += 1

    print(f"\nDone: {ok} sent, {failed} failed.")


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/send_message.py <user_id> [<user_id> ...]")
        sys.exit(1)

    try:
        user_ids = [int(arg) for arg in sys.argv[1:]]
    except ValueError:
        print("ERROR: all arguments must be integer user IDs.")
        sys.exit(1)

    token = load_token()
    bot = Bot(token=token)

    # Preview
    print("=" * 60)
    print("MESSAGE PREVIEW")
    print("=" * 60)
    print(MESSAGE)
    print("=" * 60)
    print(f"Recipients ({len(user_ids)}): {', '.join(str(u) for u in user_ids)}")
    print("=" * 60)

    confirm = input("Send this message? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        await bot.session.close()
        return

    print("\nSending...")
    await send_to_users(bot, user_ids)
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
