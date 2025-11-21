"""
Role Based Access System (RBAC) aiogram filters
"""
import logging
from typing import Dict, Any, Union

from aiogram.filters import Filter
from aiogram.types import TelegramObject

from app.enums.roles import Role

logger = logging.getLogger(__name__)


class HasRole(Filter):
    """
    Фильтр для проверки ролей пользователя.
    Пропускает только пользователей с указанными ролями.

    Usage:
        @router.message(HasRole(Role.ADMIN))
        @router.message(HasRole(Role.STAFF, Role.ADMIN))
        @router.callback_query(HasRole("volunteer", "staff"))
    """

    def __init__(self, *roles: Union[str, Role]):
        """
        Args:
            *roles: Роли, которые должны быть у пользователя для прохождения фильтра
        """
        self.required_roles = set()
        for role in roles:
            if isinstance(role, Role):
                self.required_roles.add(role.value)
            else:
                self.required_roles.add(str(role))

    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        """
        Проверяет, есть ли у пользователя требуемые роли

        Args:
            event: Telegram событие
            **data: Данные контекста (включая roles из middleware)

        Returns:
            True если у пользователя есть хотя бы одна из требуемых ролей
        """
        user_roles = data.get("roles", set())

        # Преобразуем роли в строки для сравнения
        user_roles_str = {str(role) for role in user_roles}

        has_access = bool(self.required_roles & user_roles_str)

        if not has_access:
            # Логируем попытку несанкционированного доступа
            current_user = data.get("current_user")
            user_id = current_user.user_id if current_user else "unknown"
            logger.debug("Access denied for user %s. Required: %s, User has: %s",
                         user_id, self.required_roles, user_roles_str)

        return has_access


class IsNotBanned(Filter):
    """
    Фильтр для проверки, что пользователь не заблокирован.
    Полезен в дополнение к другим фильтрам.
    """
    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        user_roles = data.get("roles", set())
        is_not_banned = Role.BANNED.value not in {str(role) for role in user_roles}

        current_user = data.get("current_user")
        user_id = current_user.user_id if current_user else "unknown"

        logger.debug("IsNotBanned filter for user %s: roles=%s, result=%s",
                     user_id, user_roles, is_not_banned
        )

        return is_not_banned
