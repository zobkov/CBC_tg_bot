"""
Роутеры для системы ролей
"""

from .public import router as public_router
from .guest import router as guest_router  
from .volunteer import router as volunteer_router
from .staff import router as staff_router
from .admin import router as admin_router

__all__ = [
    "public_router",
    "guest_router", 
    "volunteer_router",
    "staff_router", 
    "admin_router"
]