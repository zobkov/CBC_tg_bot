"""
Валидаторы доступа для aiogram-dialog с системой ролей
"""
import logging
from typing import Dict, Any, Set, Union

from aiogram.types import TelegramObject
from aiogram_dialog.api.protocols import StackAccessValidator

from app.enums.roles import Role

logger = logging.getLogger(__name__)


class RolesAccessValidator(StackAccessValidator):
    """
    Валидатор доступа к диалогам на основе ролей пользователя
    
    Используется для ограничения доступа к определенным диалогам
    в зависимости от ролей пользователя
    """

    def __init__(self, required_roles: Set[Union[str, Role]] = None):
        """
        Args:
            required_roles: Набор ролей, необходимых для доступа к диалогу
                           Если None - доступ разрешен всем (кроме banned)
        """
        if required_roles is None:
            self.required_roles = set()
            self.allow_all = True
        else:
            self.required_roles = set()
            for role in required_roles:
                if isinstance(role, Role):
                    self.required_roles.add(role.value)
                else:
                    self.required_roles.add(str(role))
            self.allow_all = False

    async def is_allowed(
        self, 
        stack, 
        context, 
        event: TelegramObject, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Проверяет, разрешен ли доступ к диалогу для пользователя
        
        Args:
            stack: Стек диалогов
            context: Контекст диалога
            event: Telegram событие
            data: Данные контекста (включая roles из middleware)
            
        Returns:
            True если доступ разрешен, False иначе
        """
        user_roles = data.get("roles", set())
        user_roles_str = {str(role) for role in user_roles}
        
        # Запрещаем доступ заблокированным пользователям
        if Role.BANNED.value in user_roles_str:
            logger.warning("Access denied: user is banned")
            return False
        
        # Если разрешен доступ всем (кроме banned)
        if self.allow_all:
            return True
        
        # Проверяем наличие требуемых ролей
        has_access = bool(self.required_roles & user_roles_str)
        
        if not has_access:
            current_user = data.get("current_user")
            user_id = current_user.user_id if current_user else "unknown"
            logger.debug(
                f"Dialog access denied for user {user_id}. "
                f"Required: {self.required_roles}, User has: {user_roles_str}"
            )
        
        return has_access


class AdminOnlyValidator(RolesAccessValidator):
    """Валидатор для диалогов, доступных только администраторам"""
    
    def __init__(self):
        super().__init__({Role.ADMIN})


class StaffValidator(RolesAccessValidator):
    """Валидатор для диалогов, доступных сотрудникам и админам"""
    
    def __init__(self):
        super().__init__({Role.STAFF, Role.ADMIN})


class VolunteerValidator(RolesAccessValidator):
    """Валидатор для диалогов, доступных волонтёрам и выше"""
    
    def __init__(self):
        super().__init__({Role.VOLUNTEER, Role.STAFF, Role.ADMIN})


class HierarchyValidator(StackAccessValidator):
    """
    Валидатор на основе иерархии ролей
    Разрешает доступ пользователям с ролью не ниже указанной
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

    async def is_allowed(
        self, 
        stack, 
        context, 
        event: TelegramObject, 
        data: Dict[str, Any]
    ) -> bool:
        user_roles = data.get("roles", set())
        user_roles_str = {str(role) for role in user_roles}
        
        min_level = self.ROLE_HIERARCHY.get(self.min_role, 0)
        
        # Проверяем, есть ли у пользователя роль с достаточным уровнем
        for role in user_roles_str:
            role_level = self.ROLE_HIERARCHY.get(role, 0)
            if role_level >= min_level:
                return True
        
        return False


class ConditionalValidator(StackAccessValidator):
    """
    Условный валидатор, позволяющий настраивать доступ на основе 
    дополнительных условий помимо ролей
    """

    def __init__(
        self, 
        required_roles: Set[Union[str, Role]] = None,
        additional_check=None
    ):
        """
        Args:
            required_roles: Требуемые роли
            additional_check: Дополнительная функция проверки
                            Принимает (event, data) и возвращает bool
        """
        if required_roles is None:
            self.required_roles = set()
        else:
            self.required_roles = set()
            for role in required_roles:
                if isinstance(role, Role):
                    self.required_roles.add(role.value)
                else:
                    self.required_roles.add(str(role))
        
        self.additional_check = additional_check

    async def is_allowed(
        self, 
        stack, 
        context, 
        event: TelegramObject, 
        data: Dict[str, Any]
    ) -> bool:
        user_roles = data.get("roles", set())
        user_roles_str = {str(role) for role in user_roles}
        
        # Проверяем роли
        if self.required_roles and not (self.required_roles & user_roles_str):
            return False
        
        # Дополнительная проверка
        if self.additional_check:
            try:
                if not await self.additional_check(event, data):
                    return False
            except Exception as e:
                logger.error(f"Error in additional check: {e}")
                return False
        
        return True


def create_forbidden_handler():
    """
    Создает обработчик для случаев запрещенного доступа к диалогам
    
    Returns:
        Функция-обработчик для недоступных диалогов
    """
    async def forbidden_handler(
        event: TelegramObject, 
        aiogd_stack_forbidden: bool = None,
        **kwargs
    ):
        """Обработчик запрещенного доступа к диалогу"""
        if aiogd_stack_forbidden:
            if hasattr(event, 'answer'):
                await event.answer(
                    "⛔ <b>Доступ запрещён</b>\n\n"
                    "У вас нет доступа к этому разделу.\n"
                    "Обратитесь к администратору, если считаете это ошибкой."
                )
            elif hasattr(event, 'message') and hasattr(event.message, 'answer'):
                await event.message.answer(
                    "⛔ <b>Доступ запрещён</b>\n\n"
                    "У вас нет доступа к этому разделу.\n"
                    "Обратитесь к администратору, если считаете это ошибкой."
                )
    
    return forbidden_handler