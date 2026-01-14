"""
Data getters used across the guest dialogs.
"""

import logging
from typing import Any

from aiogram.types import User
from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB

from app.infrastructure.database.models.broadcasts import BroadcastModel
from app.infrastructure.database.models.user_subscriptions import UserSubscriptionModel
from config.config import Config, load_config


logger = logging.getLogger(__name__)

def _get_config(dialog_manager: DialogManager) -> Config | None:
    config: Config | None = dialog_manager.middleware_data.get("config")
    if config:
        return config

    dispatcher = (
        dialog_manager.middleware_data.get("_dispatcher")
        or dialog_manager.middleware_data.get("dispatcher")
        or dialog_manager.middleware_data.get("dp")
    )
    if dispatcher:
        config = dispatcher.get("config")
        if config:
            return config

    return load_config()


async def get_broadcast_subscriptions(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None

    if db and user:
        try:
            broadcasts : list[BroadcastModel] = await db.broadcasts.list_all()
            subscriptions : list[UserSubscriptionModel] = await db.user_subscriptions.get_user_subscriptions(user_id=user.id)
        except Exception as e:
            logging.error(e)
        
        broadcast_subscription_status = ""
        subscription = None

        for broadcast in broadcasts:
            if not broadcast.enabled:
                pass

            for i in subscriptions:
                if i.broadcast_id == broadcast.id:
                    subscription = i
            
            if not subscription:
                status = "❌ Подписка отключена"
                emoji = "📪"
            elif not subscription.unsubscribed_at:
                status = "✅ Подписка активна"
                emoji = "📬"
            else:
                status = "❌ Подписка отключена"
                emoji = "📪"

            broadcast_subscription_status += f"\n{emoji} <b>{broadcast.title}</b>\n<i>{broadcast.description}</i>\nСтатус: {status}\n\n"

        return {
        "broadcast_subscription_status": broadcast_subscription_status
    }

    return {
        "broadcast_subscription_status": None
    }


async def get_broadcasts_names(
    dialog_manager: DialogManager,
    event_from_user: User,
    **_kwargs: Any,
) -> dict[str, Any]:
    
    db: DB | None = dialog_manager.middleware_data.get("db")
    event = getattr(dialog_manager, "event", None)
    user = getattr(event, "from_user", None) if event else None


    if db:
        try:
            broadcasts : list[BroadcastModel] = await db.broadcasts.list_all()
        except Exception as e:
            logging.error(e)
        
        broadcasts_names : list[tuple] = []

        for i in broadcasts:
            broadcasts_names.append((i.title, i.key))

        return {
            "broadcasts" : broadcasts_names
        }

    return {
        "broadcasts" : None
    }