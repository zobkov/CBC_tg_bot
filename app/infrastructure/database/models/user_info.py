from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base

from app.infrastructure.database.models.types import intpk, updated, created


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


@dataclass(slots=True)
class UsersInfoModel(BaseModel):
    user_id: int
    id: int | None = None
    created: datetime | None = None
    updated: datetime | None = None
    full_name: str | None = None
    email: str | None = None
    username: str | None = None  # telegram username, may be empty
    education: str | None = None
    university_course: str | None = None
    occupation: str | None = None

    def normalized_copy(self) -> "UsersInfoModel":
        return replace(
            self,
            full_name=_normalize_optional(self.full_name),
            email=_normalize_optional(self.email),
            username=_normalize_optional(self.username),
            education=_normalize_optional(self.education),
            university_course=_normalize_optional(self.university_course),
            occupation=_normalize_optional(self.occupation),
        )

    def as_db_payload(self) -> dict[str, Any]:
        normalized = self.normalized_copy()
        payload: dict[str, Any] = {
            "user_id": normalized.user_id,
            "full_name": normalized.full_name,
            "email": normalized.email,
            "username": normalized.username,
            "education": normalized.education,
            "university_course": normalized.university_course,
            "occupation": normalized.occupation,
        }
        if normalized.id is not None:
            payload["id"] = normalized.id
        if normalized.created is not None:
            payload["created"] = normalized.created
        if normalized.updated is not None:
            payload["updated"] = normalized.updated
        return payload

    @classmethod
    def from_orm(cls, entity: "UsersInfo") -> "UsersInfoModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            created=entity.created,
            updated=entity.updated,
            full_name=entity.full_name,
            email=entity.email,
            username=entity.username,
            education=entity.education,
            university_course=entity.university_course,
            occupation=entity.occupation,
        )




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

    def to_model(self) -> UsersInfoModel:
        return UsersInfoModel.from_orm(self)
