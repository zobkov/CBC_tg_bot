"""
Фильтры для системы контроля доступа на основе ролей (RBAC)
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
            logger.debug(
                f"Access denied for user {user_id}. Required: {self.required_roles}, "
                f"User has: {user_roles_str}"
            )
        
        return has_access


class HasAnyRole(Filter):
    """
    Фильтр для проверки наличия любой роли у пользователя.
    Пропускает пользователей с любой из указанных ролей.
    """

    def __init__(self, *roles: Union[str, Role]):
        """
        Args:
            *roles: Любая из этих ролей позволит пройти фильтр
        """
        self.allowed_roles = set()
        for role in roles:
            if isinstance(role, Role):
                self.allowed_roles.add(role.value)
            else:
                self.allowed_roles.add(str(role))

    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        user_roles = data.get("roles", set())
        user_roles_str = {str(role) for role in user_roles}
        return bool(self.allowed_roles & user_roles_str)


class HasAllRoles(Filter):
    """
    Фильтр для проверки наличия всех указанных ролей у пользователя.
    Пропускает только пользователей, у которых есть ВСЕ указанные роли.
    """

    def __init__(self, *roles: Union[str, Role]):
        """
        Args:
            *roles: Все эти роли должны быть у пользователя
        """
        self.required_roles = set()
        for role in roles:
            if isinstance(role, Role):
                self.required_roles.add(role.value)
            else:
                self.required_roles.add(str(role))

    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        user_roles = data.get("roles", set())
        user_roles_str = {str(role) for role in user_roles}
        return self.required_roles.issubset(user_roles_str)


class IsAdmin(Filter):
    """
    Упрощенный фильтр для проверки администраторских прав.
    """

    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        user_roles = data.get("roles", set())
        return Role.ADMIN.value in {str(role) for role in user_roles}


class IsNotBanned(Filter):
    """
    Фильтр для проверки, что пользователь не заблокирован.
    Полезен в дополнение к другим фильтрам.
    """

    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        user_roles = data.get("roles", set())
        return Role.BANNED.value not in {str(role) for role in user_roles}


class RoleHierarchy(Filter):
    """
    Фильтр на основе иерархии ролей.
    Пропускает пользователей с ролью не ниже указанной.
    """

    # Иерархия ролей (больше = выше права)
    ROLE_HIERARCHY = {
        Role.BANNED.value: 0,
        Role.GUEST.value: 1,
        Role.VOLUNTEER.value: 2,
        Role.STAFF.value: 3,
        Role.ADMIN.value: 4,
    }

    def __init__(self, min_role: Union[str, Role]):
        """
        Args:
            min_role: Минимальная роль для доступа
        """
        if isinstance(min_role, Role):
            self.min_role = min_role.value
        else:
            self.min_role = str(min_role)

    async def __call__(self, event: TelegramObject, **data: Dict[str, Any]) -> bool:
        user_roles = data.get("roles", set())
        user_roles_str = {str(role) for role in user_roles}
        
        min_level = self.ROLE_HIERARCHY.get(self.min_role, 0)
        
        # Проверяем, есть ли у пользователя роль с достаточным уровнем
        for role in user_roles_str:
            role_level = self.ROLE_HIERARCHY.get(role, 0)
            if role_level >= min_level:
                return True
        
        return False