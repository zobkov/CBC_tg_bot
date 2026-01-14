from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import UniqueConstraint, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, DateTime, text

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base
from app.infrastructure.database.models.types import intpk, created


@dataclass(slots=True)
class UserSubscriptionModel(BaseModel):
	id: int
	user_id: int
	broadcast_id: int
	subscribed_at: datetime
	unsubscribed_at: datetime | None
	preferences: dict | None


class UserSubscriptions(Base):
	__tablename__ = "user_subscriptions"

	id: Mapped[intpk]

	user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

	broadcast_id: Mapped[int] = mapped_column(ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False)

	subscribed_at: Mapped[created]

	unsubscribed_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=True
	)

	preferences: Mapped[dict] = mapped_column(JSONB, nullable=True)

	__table_args__ = (
		UniqueConstraint("user_id", "broadcast_id", name="uq_user_broadcast"),
	)

	def to_model(self) -> UserSubscriptionModel:
		return UserSubscriptionModel(
			id=self.id,
			user_id=self.user_id,
			broadcast_id=self.broadcast_id,
			subscribed_at=self.subscribed_at,
			unsubscribed_at=self.unsubscribed_at,
			preferences=self.preferences,
		)

