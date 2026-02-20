from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base
from app.infrastructure.database.models.types import intpk, created


@dataclass(slots=True)
class OnlineEventModel(BaseModel):
	id: int
	slug: str
	alias: str
	title: str
	speaker: str | None
	description: str | None
	url: str | None
	start_at: datetime
	end_at: datetime
	is_active: bool
	created_at: datetime


class OnlineEvents(Base):
	__tablename__ = "online_events"

	id: Mapped[intpk]

	slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

	alias: Mapped[str] = mapped_column(String(50), nullable=False)

	title: Mapped[str] = mapped_column(String(255), nullable=False)

	speaker: Mapped[str] = mapped_column(String(255), nullable=True)

	description: Mapped[str] = mapped_column(Text, nullable=True)

	url: Mapped[str] = mapped_column(String(500), nullable=True)

	start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

	end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

	created_at: Mapped[created]

	def to_model(self) -> OnlineEventModel:
		return OnlineEventModel(
			id=self.id,
			slug=self.slug,
			alias=self.alias,
			title=self.title,
			speaker=self.speaker,
			description=self.description,
			url=self.url,
			start_at=self.start_at,
			end_at=self.end_at,
			is_active=self.is_active,
			created_at=self.created_at,
		)
