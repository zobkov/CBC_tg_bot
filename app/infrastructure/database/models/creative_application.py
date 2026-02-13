"""Models for creative casting applications."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.models.types import created, intpk, updated
from app.infrastructure.database.orm.base import Base


def _normalize_optional(value: str | None) -> str | None:
    """Strip whitespace and convert empty strings to None."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


@dataclass(slots=True)
class CreativeApplicationModel(BaseModel):
    """Business logic model for creative applications."""

    user_id: int
    contact: str
    direction: str  # 'ceremony' or 'fair'

    # Ceremony fields (nullable)
    ceremony_stage_experience: str | None = None
    ceremony_motivation: str | None = None
    ceremony_can_attend_md: bool | None = None
    ceremony_rehearsal_frequency: str | None = None
    ceremony_rehearsal_duration: str | None = None
    ceremony_timeslots: list[str] | None = None
    ceremony_cloud_link: str | None = None

    # Fair fields (nullable)
    fair_roles: list[str] | None = None
    fair_motivation: str | None = None
    fair_experience: str | None = None
    fair_cloud_link: str | None = None

    # Auto-managed fields
    id: int | None = None
    submitted_at: datetime | None = None
    updated: datetime | None = None

    def normalized_copy(self) -> "CreativeApplicationModel":
        """Return a copy with normalized text fields."""
        return replace(
            self,
            contact=_normalize_optional(self.contact),
            ceremony_stage_experience=_normalize_optional(self.ceremony_stage_experience),
            ceremony_motivation=_normalize_optional(self.ceremony_motivation),
            ceremony_rehearsal_frequency=_normalize_optional(
                self.ceremony_rehearsal_frequency
            ),
            ceremony_rehearsal_duration=_normalize_optional(
                self.ceremony_rehearsal_duration
            ),
            ceremony_cloud_link=_normalize_optional(self.ceremony_cloud_link),
            fair_motivation=_normalize_optional(self.fair_motivation),
            fair_experience=_normalize_optional(self.fair_experience),
            fair_cloud_link=_normalize_optional(self.fair_cloud_link),
        )

    def as_db_payload(self) -> dict[str, Any]:
        """Convert to database payload for insert/update operations."""
        normalized = self.normalized_copy()
        payload: dict[str, Any] = {
            "user_id": normalized.user_id,
            "contact": normalized.contact,
            "direction": normalized.direction,
            "ceremony_stage_experience": normalized.ceremony_stage_experience,
            "ceremony_motivation": normalized.ceremony_motivation,
            "ceremony_can_attend_md": normalized.ceremony_can_attend_md,
            "ceremony_rehearsal_frequency": normalized.ceremony_rehearsal_frequency,
            "ceremony_rehearsal_duration": normalized.ceremony_rehearsal_duration,
            "ceremony_timeslots": normalized.ceremony_timeslots,
            "ceremony_cloud_link": normalized.ceremony_cloud_link,
            "fair_roles": normalized.fair_roles,
            "fair_motivation": normalized.fair_motivation,
            "fair_experience": normalized.fair_experience,
            "fair_cloud_link": normalized.fair_cloud_link,
        }
        # Include optional fields if present
        if normalized.id is not None:
            payload["id"] = normalized.id
        if normalized.submitted_at is not None:
            payload["submitted_at"] = normalized.submitted_at
        if normalized.updated is not None:
            payload["updated"] = normalized.updated
        return payload

    @classmethod
    def from_orm(cls, entity: "CreativeApplications") -> "CreativeApplicationModel":
        """Create model from ORM entity."""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            contact=entity.contact,
            direction=entity.direction,
            ceremony_stage_experience=entity.ceremony_stage_experience,
            ceremony_motivation=entity.ceremony_motivation,
            ceremony_can_attend_md=entity.ceremony_can_attend_md,
            ceremony_rehearsal_frequency=entity.ceremony_rehearsal_frequency,
            ceremony_rehearsal_duration=entity.ceremony_rehearsal_duration,
            ceremony_timeslots=entity.ceremony_timeslots,
            ceremony_cloud_link=entity.ceremony_cloud_link,
            fair_roles=entity.fair_roles,
            fair_motivation=entity.fair_motivation,
            fair_experience=entity.fair_experience,
            fair_cloud_link=entity.fair_cloud_link,
            submitted_at=entity.submitted_at,
            updated=entity.updated,
        )


class CreativeApplications(Base):
    """ORM model for creative_applications table."""

    __tablename__ = "creative_applications"

    id: Mapped[intpk]

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    contact: Mapped[str] = mapped_column(Text, nullable=False)

    direction: Mapped[str] = mapped_column(Text, nullable=False)

    # Ceremony branch fields
    ceremony_stage_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceremony_motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceremony_can_attend_md: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ceremony_rehearsal_frequency: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceremony_rehearsal_duration: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceremony_timeslots: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    ceremony_cloud_link: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Fair branch fields
    fair_roles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    fair_motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    fair_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    fair_cloud_link: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    submitted_at: Mapped[created]
    updated: Mapped[updated]

    def to_model(self) -> CreativeApplicationModel:
        """Convert ORM entity to business model."""
        return CreativeApplicationModel.from_orm(self)
