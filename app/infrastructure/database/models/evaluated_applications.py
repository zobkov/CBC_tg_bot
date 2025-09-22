from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.database.models.base import BaseModel


@dataclass
class EvaluatedApplicationModel(BaseModel):
    id: int
    user_id: int
    accepted_1: bool
    accepted_2: bool
    accepted_3: bool
    created: datetime
    updated: datetime