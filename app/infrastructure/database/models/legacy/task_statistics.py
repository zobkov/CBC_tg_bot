from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.infrastructure.database.models.base import BaseModel


@dataclass
class TaskStatisticsModel(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    date_first_accessed: datetime