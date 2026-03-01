from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base
from app.infrastructure.database.models.types import intpk, created, updated


@dataclass(slots=True)
class UserMentorsModel(BaseModel):
    id: int
    user_id: int
    lessons_approved: list[str]
    mentor_contacts: str | None
    created_at: datetime
    updated_at: datetime


class UserMentors(Base):
    __tablename__ = "user_mentors"

    id: Mapped[intpk]

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    lessons_approved: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    mentor_contacts: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    def to_model(self) -> UserMentorsModel:
        return UserMentorsModel(
            id=self.id,
            user_id=self.user_id,
            lessons_approved=list(self.lessons_approved or []),
            mentor_contacts=self.mentor_contacts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
