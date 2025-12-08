from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import Boolean, DateTime, BigInteger, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base

from app.infrastructure.database.models.types import intpk, updated, created


def _normalize_roles(raw: Any) -> list[str]:
    if raw is None:
        return ["guest"]
    if isinstance(raw, list):
        return raw or ["guest"]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed or ["guest"]
        except json.JSONDecodeError:
            pass
        return [raw] if raw else ["guest"]
    return ["guest"]


@dataclass(slots=True)
class UsersModel(BaseModel):
    user_id: int
    created: datetime
    is_alive: bool = True
    is_blocked: bool = False
    roles: list[str] = field(default_factory=lambda: ["guest"])

    @classmethod
    def from_orm(cls, entity: "Users") -> "UsersModel":
        return cls(
            user_id=entity.user_id,
            created=entity.created,
            is_alive=entity.is_alive,
            is_blocked=entity.is_blocked,
            roles=_normalize_roles(entity.roles),
        )

    def __post_init__(self) -> None:
        self.roles = _normalize_roles(self.roles)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, roles: Iterable[str]) -> bool:
        return bool(set(roles) & set(self.roles))

    def is_admin(self) -> bool:
        return self.has_role("admin")

    def is_banned(self) -> bool:
        return self.has_role("banned")

    @property
    def language(self) -> str:
        return "ru"

    @property
    def submission_status(self) -> str:
        return "not_submitted"

    @property
    def task_1_submitted(self) -> bool:
        return False

    @property
    def task_2_submitted(self) -> bool:
        return False

    @property
    def task_3_submitted(self) -> bool:
        return False

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "created": self.created.isoformat(),
            "is_alive": self.is_alive,
            "is_blocked": self.is_blocked,
            "roles": self.roles,
        }

    @classmethod
    def from_cache(cls, payload: dict[str, Any]) -> "UsersModel":
        created_raw = payload.get("created")
        if isinstance(created_raw, str):
            created_dt = datetime.fromisoformat(created_raw)
        elif isinstance(created_raw, datetime):
            created_dt = created_raw
        else:
            created_dt = datetime.now(timezone.utc)
        return cls(
            user_id=payload["user_id"],
            created=created_dt,
            is_alive=payload.get("is_alive", True),
            is_blocked=payload.get("is_blocked", False),
            roles=_normalize_roles(payload.get("roles")),
        )


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    created: Mapped[created]

    updated: Mapped[updated]

    is_alive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    
    roles: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[\"guest\"]'::jsonb"),
    )

    def to_model(self) -> UsersModel:
        return UsersModel.from_orm(self)
