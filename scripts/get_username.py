#!/usr/bin/env python3
"""
Fetch Telegram username(s) by user_id via the bot (getChat API call).

Usage:
    python3 scripts/get_username.py <user_id> [<user_id> ...]

Example:
    python3 scripts/get_username.py 123456789 987654321
"""

import asyncio
import sys
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import load_config


async def fetch_usernames(user_ids: list[int]) -> None:
    config = load_config()
    bot = Bot(token=config.tg_bot.token)

    try:
        for uid in user_ids:
            try:
                chat = await bot.get_chat(chat_id=uid)
                username = f"@{chat.username}" if chat.username else "(нет username)"
                full_name = chat.full_name or ""
                print(f"{uid}\t{username}\t{full_name}")
            except TelegramForbiddenError:
                print(f"{uid}\tERROR: бот заблокирован пользователем")
            except TelegramBadRequest as e:
                print(f"{uid}\tERROR: {e}")
    finally:
        await bot.session.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/get_username.py <user_id> [<user_id> ...]")
        sys.exit(1)

    user_ids: list[int] = []
    for arg in sys.argv[1:]:
        if arg.isdigit():
            user_ids.append(int(arg))
        else:
            print(f"Пропускаю некорректный user_id: {arg!r}")

    if not user_ids:
        print("Нет корректных user_id для запроса.")
        sys.exit(1)

    asyncio.run(fetch_usernames(user_ids))


if __name__ == "__main__":
    main()
