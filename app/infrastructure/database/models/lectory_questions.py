"""SQLAlchemy model for lectory Q&A questions."""
from __future__ import annotations

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.types import created, intpk
from app.infrastructure.database.orm.base import Base


class LectoryQuestion(Base):
    """User question submitted for a lectory event.

    ``answer_text`` is NULL until an admin fills it in.
    """

    __tablename__ = "lectory_questions"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    event_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(256), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[created]
