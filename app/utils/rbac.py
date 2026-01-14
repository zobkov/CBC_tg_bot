"""Helper functions for RBAC"""
import logging
import asyncio
import inspect
from typing import Any

from aiogram.fsm.storage.redis import RedisStorage


logger = logging.getLogger(__name__)


LOCK_REDIS_KEY = "bot:lock_mode"


async def is_lock_mode_enabled(storage: RedisStorage) -> bool:
    """Checks whether lock mode is enabled"""
    try:
        redis = storage.redis
        result = await redis.get(LOCK_REDIS_KEY)
        logger.debug("Redis value for key %s: %s (type: {type(result)})",
                     LOCK_REDIS_KEY, result)

        # Redis returns bytes, compare to b"1"
        is_enabled = result == b"1" if result else False
        logger.debug("Lock mode status: %s", is_enabled)
        return is_enabled
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.exception("Exception while checking lock mode in Redis: %s", e)
        return False
