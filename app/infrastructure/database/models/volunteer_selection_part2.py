"""ORM model and business-logic dataclass for volunteer selection part 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.models.types import created, intpk, updated
from app.infrastructure.database.orm.base import Base


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


@dataclass(slots=True)
class VolSelPart2Model(BaseModel):
    """Business logic model for volunteer selection part 2 answers."""

    user_id: int

    # Written questions (Q1–Q6 required; Q7 branch optional)
    q1_kbc_ordinal: str | None = None          # one of: "1ый","2ой","3ий","4ый","5ый"
    q2_kbc_date: str | None = None             # free text, e.g. "25 апреля"
    q3_kbc_theme: str | None = None            # free text
    q4_team_experience: str | None = None      # long text
    q5_badge_case: str | None = None           # long text
    q6_foreign_guest_case: str | None = None   # long text
    q7_want_tour: str | None = None            # "yes" | "no"
    q7_has_tour_experience: str | None = None  # "yes" | "no" (nullable – only if q7=yes)
    q7_tour_route: str | None = None           # long text (nullable – only if q7=yes)

    # Video interview file_ids
    vq1_file_id: str | None = None
    vq2_file_id: str | None = None
    vq3_file_id: str | None = None

    # Admin review flag
    reviewed: bool = False

    # Auto-managed
    id: int | None = None
    submitted_at: datetime | None = None
    updated: datetime | None = None

    def as_db_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "user_id": self.user_id,
            "q1_kbc_ordinal": _normalize_optional(self.q1_kbc_ordinal),
            "q2_kbc_date": _normalize_optional(self.q2_kbc_date),
            "q3_kbc_theme": _normalize_optional(self.q3_kbc_theme),
            "q4_team_experience": _normalize_optional(self.q4_team_experience),
            "q5_badge_case": _normalize_optional(self.q5_badge_case),
            "q6_foreign_guest_case": _normalize_optional(self.q6_foreign_guest_case),
            "q7_want_tour": self.q7_want_tour,
            "q7_has_tour_experience": self.q7_has_tour_experience,
            "q7_tour_route": _normalize_optional(self.q7_tour_route),
            "vq1_file_id": self.vq1_file_id,
            "vq2_file_id": self.vq2_file_id,
            "vq3_file_id": self.vq3_file_id,
        }
        if self.id is not None:
            payload["id"] = self.id
        if self.submitted_at is not None:
            payload["submitted_at"] = self.submitted_at
        if self.updated is not None:
            payload["updated"] = self.updated
        return payload


class VolSelPart2(Base):
    """ORM table for volunteer_selection_part2."""

    __tablename__ = "volunteer_selection_part2"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    q1_kbc_ordinal: Mapped[str | None] = mapped_column(Text, nullable=True)
    q2_kbc_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    q3_kbc_theme: Mapped[str | None] = mapped_column(Text, nullable=True)
    q4_team_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    q5_badge_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    q6_foreign_guest_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    q7_want_tour: Mapped[str | None] = mapped_column(Text, nullable=True)
    q7_has_tour_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    q7_tour_route: Mapped[str | None] = mapped_column(Text, nullable=True)

    vq1_file_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    vq2_file_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    vq3_file_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    submitted_at: Mapped[created]
    updated: Mapped[updated]

    def to_model(self) -> VolSelPart2Model:
        return VolSelPart2Model(
            id=self.id,
            user_id=self.user_id,
            q1_kbc_ordinal=self.q1_kbc_ordinal,
            q2_kbc_date=self.q2_kbc_date,
            q3_kbc_theme=self.q3_kbc_theme,
            q4_team_experience=self.q4_team_experience,
            q5_badge_case=self.q5_badge_case,
            q6_foreign_guest_case=self.q6_foreign_guest_case,
            q7_want_tour=self.q7_want_tour,
            q7_has_tour_experience=self.q7_has_tour_experience,
            q7_tour_route=self.q7_tour_route,
            vq1_file_id=self.vq1_file_id,
            vq2_file_id=self.vq2_file_id,
            vq3_file_id=self.vq3_file_id,
            reviewed=self.reviewed,
            submitted_at=self.submitted_at,
            updated=self.updated,
        )
