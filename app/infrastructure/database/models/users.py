from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.infrastructure.database.models.base import BaseModel


@dataclass
class UsersModel(BaseModel):
    user_id: int
    created: datetime
    language: str
    is_alive: bool
    is_blocked: bool
    submission_status: str  # "not_submitted" | "submitted"
    task_1_submitted: bool = False
    task_2_submitted: bool = False
    task_3_submitted: bool = False
    roles: List[str] = None  # Список ролей пользователя
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.roles is None:
            self.roles = ["guest"]  # Роль по умолчанию
    
    def has_role(self, role: str) -> bool:
        """Проверяет, есть ли у пользователя указанная роль"""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Проверяет, есть ли у пользователя хотя бы одна из указанных ролей"""
        return bool(set(roles) & set(self.roles))
    
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return self.has_role("admin")
    
    def is_banned(self) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        return self.has_role("banned")
