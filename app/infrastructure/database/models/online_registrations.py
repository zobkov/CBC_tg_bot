from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import UniqueConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base
from app.infrastructure.database.models.types import intpk, created


@dataclass(slots=True)
class OnlineRegistrationModel(BaseModel):
	id: int
	user_id: int
	event_id: int
	status: str
	registered_at: datetime


class OnlineRegistrations(Base):
	__tablename__ = "online_registrations"

	id: Mapped[intpk]

	user_id: Mapped[int] = mapped_column(
		BigInteger, 
		ForeignKey("users.user_id", ondelete="CASCADE"), 
		nullable=False
	)

	event_id: Mapped[int] = mapped_column(
		ForeignKey("online_events.id", ondelete="CASCADE"), 
		nullable=False
	)

	status: Mapped[str] = mapped_column(
		String(20), 
		nullable=False, 
		server_default="active"
	)

	registered_at: Mapped[created]

	__table_args__ = (
		UniqueConstraint("user_id", "event_id", name="uq_user_event"),
	)

	def to_model(self) -> OnlineRegistrationModel:
		return OnlineRegistrationModel(
			id=self.id,
			user_id=self.user_id,
			event_id=self.event_id,
			status=self.status,
			registered_at=self.registered_at,
		)
