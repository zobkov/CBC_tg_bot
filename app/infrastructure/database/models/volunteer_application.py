"""Models for volunteer selection applications."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Text
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
class VolunteerApplicationModel(BaseModel):
    """Business logic model for volunteer applications."""

    user_id: int

    # Compulsory fields
    phone: str | None = None
    volunteer_dates: str | None = None  # "single" | "double"
    function: str | None = None  # "general" | "photo" | "translate"

    # General branch
    general_1_type: str | None = None  # "guest" | "volunteer" | "guest_and_volunteer" | "no"
    general_1_answer: str | None = None
    general_2: str | None = None
    general_3: str | None = None

    # Photo branch
    photo_portfolio: str | None = None
    photo_has_equipment: str | None = None  # "yes" | "no"
    photo_experience: str | None = None
    photo_key_moments: str | None = None

    # Translation branch
    translate_level: str | None = None
    translate_has_cert: str | None = None  # "yes" | "no"
    translate_cert_link: str | None = None
    translate_experience_detail: str | None = None
    translate_worked_with_foreigners: str | None = None
    translate_difficult_situation: str | None = None

    # Additional info
    additional_information: str | None = None

    # Auto-managed
    id: int | None = None
    submitted_at: datetime | None = None
    updated: datetime | None = None

    def normalized_copy(self) -> "VolunteerApplicationModel":
        """Return a copy with normalized text fields."""
        return replace(
            self,
            phone=_normalize_optional(self.phone),
            general_1_answer=_normalize_optional(self.general_1_answer),
            general_2=_normalize_optional(self.general_2),
            general_3=_normalize_optional(self.general_3),
            photo_portfolio=_normalize_optional(self.photo_portfolio),
            photo_experience=_normalize_optional(self.photo_experience),
            photo_key_moments=_normalize_optional(self.photo_key_moments),
            translate_level=_normalize_optional(self.translate_level),
            translate_cert_link=_normalize_optional(self.translate_cert_link),
            translate_experience_detail=_normalize_optional(self.translate_experience_detail),
            translate_worked_with_foreigners=_normalize_optional(self.translate_worked_with_foreigners),
            translate_difficult_situation=_normalize_optional(self.translate_difficult_situation),
            additional_information=_normalize_optional(self.additional_information),
        )

    def as_db_payload(self) -> dict[str, Any]:
        """Convert to database payload for insert/update operations."""
        normalized = self.normalized_copy()
        payload: dict[str, Any] = {
            "user_id": normalized.user_id,
            "phone": normalized.phone,
            "volunteer_dates": normalized.volunteer_dates,
            "function": normalized.function,
            "general_1_type": normalized.general_1_type,
            "general_1_answer": normalized.general_1_answer,
            "general_2": normalized.general_2,
            "general_3": normalized.general_3,
            "photo_portfolio": normalized.photo_portfolio,
            "photo_has_equipment": normalized.photo_has_equipment,
            "photo_experience": normalized.photo_experience,
            "photo_key_moments": normalized.photo_key_moments,
            "translate_level": normalized.translate_level,
            "translate_has_cert": normalized.translate_has_cert,
            "translate_cert_link": normalized.translate_cert_link,
            "translate_experience_detail": normalized.translate_experience_detail,
            "translate_worked_with_foreigners": normalized.translate_worked_with_foreigners,
            "translate_difficult_situation": normalized.translate_difficult_situation,
            "additional_information": normalized.additional_information,
        }
        if normalized.id is not None:
            payload["id"] = normalized.id
        if normalized.submitted_at is not None:
            payload["submitted_at"] = normalized.submitted_at
        if normalized.updated is not None:
            payload["updated"] = normalized.updated
        return payload

    @classmethod
    def from_orm(cls, entity: "VolunteerApplications") -> "VolunteerApplicationModel":
        """Create model from ORM entity."""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            phone=entity.phone,
            volunteer_dates=entity.volunteer_dates,
            function=entity.function,
            general_1_type=entity.general_1_type,
            general_1_answer=entity.general_1_answer,
            general_2=entity.general_2,
            general_3=entity.general_3,
            photo_portfolio=entity.photo_portfolio,
            photo_has_equipment=entity.photo_has_equipment,
            photo_experience=entity.photo_experience,
            photo_key_moments=entity.photo_key_moments,
            translate_level=entity.translate_level,
            translate_has_cert=entity.translate_has_cert,
            translate_cert_link=entity.translate_cert_link,
            translate_experience_detail=entity.translate_experience_detail,
            translate_worked_with_foreigners=entity.translate_worked_with_foreigners,
            translate_difficult_situation=entity.translate_difficult_situation,
            additional_information=entity.additional_information,
            submitted_at=entity.submitted_at,
            updated=entity.updated,
        )


class VolunteerApplications(Base):
    """ORM model for volunteer_applications table."""

    __tablename__ = "volunteer_applications"

    id: Mapped[intpk]

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    # Compulsory
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    volunteer_dates: Mapped[str | None] = mapped_column(Text, nullable=True)
    function: Mapped[str | None] = mapped_column(Text, nullable=True)

    # General branch
    general_1_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_1_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_3: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Photo branch
    photo_portfolio: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_has_equipment: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_key_moments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Translation branch
    translate_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    translate_has_cert: Mapped[str | None] = mapped_column(Text, nullable=True)
    translate_cert_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    translate_experience_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    translate_worked_with_foreigners: Mapped[str | None] = mapped_column(Text, nullable=True)
    translate_difficult_situation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional info
    additional_information: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    submitted_at: Mapped[created]
    updated: Mapped[updated]

    def to_model(self) -> VolunteerApplicationModel:
        """Convert ORM entity to business model."""
        return VolunteerApplicationModel.from_orm(self)
