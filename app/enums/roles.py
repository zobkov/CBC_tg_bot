"""
Роли пользователей в системе CBC Crew Selection Bot
"""
from enum import StrEnum


class Role(StrEnum):
    """Роли пользователей в боте"""
    ADMIN = "admin"
    STAFF = "staff"  
    VOLUNTEER = "volunteer"
    GUEST = "guest"
    BANNED = "banned"

    @classmethod
    def get_all_roles(cls) -> list[str]:
        """Получить список всех ролей"""
        return [role.value for role in cls]

    @classmethod
    def get_default_role(cls) -> str:
        """Получить роль по умолчанию для новых пользователей"""
        return cls.GUEST.value

    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Проверить валидность роли"""
        return role in cls.get_all_roles()

    def has_privilege_over(self, other_role: str) -> bool:
        """Проверить, имеет ли текущая роль привилегии над другой ролью"""
        hierarchy = {
            self.BANNED: 0,
            self.GUEST: 1,
            self.VOLUNTEER: 2,
            self.STAFF: 3,
            self.ADMIN: 4,
        }
        
        return hierarchy.get(self, 0) > hierarchy.get(other_role, 0)