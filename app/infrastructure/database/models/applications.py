from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.bot.enums.application_status import ApplicationStatus
from app.infrastructure.database.models.base import BaseModel


@dataclass
class ApplicationsModel(BaseModel):
    id: int
    user_id: int
    status: ApplicationStatus
    created: datetime
    updated: datetime
    
    # Форма первого этапа
    full_name: Optional[str] = None
    university: Optional[str] = None
    course: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_username: Optional[str] = None
    how_found_kbk: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    experience: Optional[str] = None
    motivation: Optional[str] = None
    resume_local_path: Optional[str] = None
    resume_google_drive_url: Optional[str] = None
    previous_department: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = ApplicationStatus(self.status)
