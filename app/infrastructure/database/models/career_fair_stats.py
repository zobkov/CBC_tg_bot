"""SQLAlchemy model for career fair event statistics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.types import created, intpk
from app.infrastructure.database.orm.base import Base


@dataclass(slots=True)
class CareerFairEventModel:
    id: int
    user_id: int
    event_type: str
    track_key: str | None
    company_key: str | None
    created_at: datetime


class CareerFairEvent(Base):
    """Tracks user interactions inside the Ярмарка карьеры dialog.

    event_type values:
      - 'track_view'     — user opened a track's company list
      - 'company_view'   — user opened a company detail screen
      - 'vacancies_view' — user opened the vacancies list for a company
    """

    __tablename__ = "career_fair_events"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    track_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[created]

    def to_model(self) -> CareerFairEventModel:
        return CareerFairEventModel(
            id=self.id,
            user_id=self.user_id,
            event_type=self.event_type,
            track_key=self.track_key,
            company_key=self.company_key,
            created_at=self.created_at,
        )
