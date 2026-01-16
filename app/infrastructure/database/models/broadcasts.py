
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base
from app.infrastructure.database.models.types import intpk, created


@dataclass(slots=True)
class BroadcastModel(BaseModel):
	id: int
	key: str
	title: str | None
	description: str | None
	channel: str | None
	enabled: bool
	created_at: datetime


class Broadcasts(Base):
	__tablename__ = "broadcasts"

	id: Mapped[intpk]

	key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

	title: Mapped[str] = mapped_column(Text, nullable=True)

	description: Mapped[str] = mapped_column(Text, nullable=True)

	channel: Mapped[str] = mapped_column(String(32), nullable=True)

	enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

	created_at: Mapped[created]

	__table_args__ = (
		UniqueConstraint("key", name="uq_broadcasts_key"),
	)

	def to_model(self) -> BroadcastModel:
		return BroadcastModel(
			id=self.id,
			key=self.key,
			title=self.title,
			description=self.description,
			channel=self.channel,
			enabled=self.enabled,
			created_at=self.created_at,
		)

