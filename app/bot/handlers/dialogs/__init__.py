"""
Хендлеры диалогов по ролям
"""

from .guest import guest_dialogs_router
from .volunteer import volunteer_dialogs_router  
from .staff import staff_dialogs_router
from .admin import admin_dialogs_router

__all__ = [
    "guest_dialogs_router",
    "volunteer_dialogs_router",
    "staff_dialogs_router", 
    "admin_dialogs_router"
]