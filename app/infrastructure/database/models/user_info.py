from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Annotated

from sqlalchemy import Boolean, DateTime, BigInteger, text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base

from app.infrastructure.database.models.types import intpk, updated, created

@dataclass(slots=True)
class UsersInfoModel(BaseModel):
    id: int
    user_id: int
    created: datetime
    updated: datetime
    full_name: str = None
    email: str = None
    username: str # from telegram; might be empty but should always be checked for
    education: str = None
    university_course: str = None
    occupation: str = None




class UsersInfo(Base):
    __tablename__ = "user_info"

    id: Mapped[intpk]

    user_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    
    created: Mapped[created]

    updated: Mapped[updated]

    full_name: Mapped[str | None]
    email: Mapped[str | None]

    # Although this value is nullable, it must filled at all times, if a username exists
    username: Mapped[str | None]

    education: Mapped[str | None]
    university_course: Mapped[str | None]
    occupation: Mapped[str | None]




