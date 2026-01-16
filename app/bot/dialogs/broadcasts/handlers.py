"""Callback handlers for broadcast menu dialog buttons."""

from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

import logging

from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.user_subscriptions import UserSubscriptionModel




logger = logging.getLogger(__name__)



async def on_broadcast_selected(callback: CallbackQuery, widget: Any,
                            dialog_manager: DialogManager, item_id: str) -> None:
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None

    logger.debug("Selected broadcast: %s", item_id)

    try:
        if db and user:
            user_subscriptions : list[UserSubscriptionModel] = await db.user_subscriptions.get_user_subscriptions(user_id=user.id)
            broadcast = await db.broadcasts.get_by_key(key=item_id)
            existing_subscription = None
            for sub in user_subscriptions:
                if sub.broadcast_id == broadcast.id:
                    existing_subscription = sub
                    logger.debug("Found subscription for %s", existing_subscription.broadcast_id)
                    break
            

            
            if existing_subscription:
                logger.debug(existing_subscription.unsubscribed_at)
                if not existing_subscription.unsubscribed_at:
                    await db.user_subscriptions.unsubscribe(user_id=user.id, broadcast_key=item_id)
                else:
                    await db.user_subscriptions.subscribe_by_broadcast_key(user_id=user.id, broadcast_key=item_id)
            else:
                await db.user_subscriptions.subscribe_by_broadcast_key(user_id=user.id, broadcast_key=item_id)
    except Exception as e:
        logger.error(e)