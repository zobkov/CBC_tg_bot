"""Global application container for sharing non-serializable dependencies.

APScheduler serializes job arguments via pickle (when using RedisJobStore),
so Bot, Dispatcher, and session_factory cannot be passed as job args.
Instead, store them here at startup and resolve them inside job functions.
"""
from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot, Dispatcher


@dataclass
class AppContainer:
    bot: Bot
    dp: Dispatcher


_container: AppContainer | None = None


def setup_container(bot: Bot, dp: Dispatcher) -> None:
    """Call once at startup, before the timer scheduler starts."""
    global _container  # noqa: PLW0603
    _container = AppContainer(bot=bot, dp=dp)


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError(
            "AppContainer is not initialized. Call setup_container() first."
        )
    return _container
