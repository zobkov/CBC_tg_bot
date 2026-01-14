"""Helper functions for RBAC"""
import logging
import asyncio
import inspect
from typing import Any

from aiogram.fsm.storage.redis import RedisStorage


logger = logging.getLogger(__name__)


LOCK_REDIS_KEY = "bot:lock_mode"


async def is_lock_mode_enabled(storage: RedisStorage | Any) -> bool:
    """Checks whether lock mode is enabled.

    Accepts either a `RedisStorage` instance (which exposes `.redis`) or a
    raw Redis client. For synchronous clients we run the call in a thread.
    """
    try:
        # Support both RedisStorage (has `.redis`) and raw redis client
        redis_client = getattr(storage, "redis", storage)

        get_func = getattr(redis_client, "get", None)
        if get_func is None:
            logger.debug("Redis client has no `get` method: %r", redis_client)
            return False

        # Call the `get` function and handle both awaitable and immediate results.
        # Many async clients return a coroutine object when called; others may
        # return the result directly. We call it and then await if needed.
        maybe_result = get_func(LOCK_REDIS_KEY)

        if inspect.iscoroutine(maybe_result) or inspect.isawaitable(maybe_result) or hasattr(maybe_result, "__await__"):
            result = await maybe_result
        else:
            # Non-awaitable immediate result (bytes/str/None)
            result = maybe_result

        logger.debug("Redis value for key %s: %s (type: %s)", LOCK_REDIS_KEY, result, type(result))

        # Redis returns bytes for async redis-py; normalize and compare
        is_enabled = result == b"1" if result else False
        logger.debug("Lock mode status: %s", is_enabled)
        return is_enabled
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Exception while checking lock mode in Redis: %s", e)
        return False
