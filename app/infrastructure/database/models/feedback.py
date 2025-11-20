from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import BigInteger, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import BaseModel
from app.infrastructure.database.orm.base import Base


@dataclass(slots=True)
class FeedbackModel(BaseModel):
    user_id: int
    submission_status: bool = False
    task_1_accepted: bool = False
    task_2_accepted: bool = False
    task_3_accepted: bool = False
    interview_approved: bool = False
    task_1_feedback: str | None = None
    task_2_feedback: str | None = None
    task_3_feedback: str | None = None
    interview_feedback: str | None = None

    def _normalize_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    def iter_task_feedback(self) -> Iterable[tuple[int, str]]:
        mapping = (
            (1, self._normalize_text(self.task_1_feedback)),
            (2, self._normalize_text(self.task_2_feedback)),
            (3, self._normalize_text(self.task_3_feedback)),
        )
        return ((idx, text) for idx, text in mapping if text)

    def has_any_task_feedback(self) -> bool:
        return any(True for _ in self.iter_task_feedback())

    def all_tasks_declined(self) -> bool:
        return not any((self.task_1_accepted, self.task_2_accepted, self.task_3_accepted))

    def can_show_tasks_feedback(self) -> bool:
        return self.submission_status and self.all_tasks_declined() and self.has_any_task_feedback()

    def has_interview_feedback(self) -> bool:
        return bool(self._normalize_text(self.interview_feedback))

    def can_show_interview_feedback(self) -> bool:
        return (not self.interview_approved) and self.has_interview_feedback()


class Feedback(Base):
    """Aggregated legacy feedback view."""

    __tablename__ = "legacy_feedback_view"
    __table_args__ = {"info": {"is_view": True}}

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    submission_status: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_1_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_2_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_3_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    interview_approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_1_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_2_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_3_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_model(self) -> FeedbackModel:
        return FeedbackModel(
            user_id=self.user_id,
            submission_status=bool(self.submission_status),
            task_1_accepted=bool(self.task_1_accepted),
            task_2_accepted=bool(self.task_2_accepted),
            task_3_accepted=bool(self.task_3_accepted),
            interview_approved=bool(self.interview_approved),
            task_1_feedback=self.task_1_feedback,
            task_2_feedback=self.task_2_feedback,
            task_3_feedback=self.task_3_feedback,
            interview_feedback=self.interview_feedback,
        )
