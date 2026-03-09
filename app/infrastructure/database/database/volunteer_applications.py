"""Database operations for volunteer applications."""

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.volunteer_application import (
    VolunteerApplicationModel,
    VolunteerApplications,
)

logger = logging.getLogger(__name__)


class _VolunteerApplicationsDB:
    """Database operations for volunteer applications."""

    __tablename__ = "volunteer_applications"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_application(self, *, model: VolunteerApplicationModel) -> None:
        """
        Insert or update a volunteer application.

        Uses user_id as the conflict key so users can re-submit.
        """
        normalized = model.normalized_copy()
        payload = normalized.as_db_payload()

        payload.pop("id", None)
        payload.pop("submitted_at", None)
        payload.pop("updated", None)

        stmt = insert(VolunteerApplications).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[VolunteerApplications.user_id],
            set_=payload,
        )
        await self.session.execute(stmt)

        logger.info(
            "Volunteer application saved. db='%s', user_id=%d, function=%s",
            self.__tablename__,
            normalized.user_id,
            normalized.function,
        )

    async def get_application(self, *, user_id: int) -> VolunteerApplicationModel | None:
        """Retrieve a user's volunteer application."""
        stmt = select(VolunteerApplications).where(
            VolunteerApplications.user_id == user_id
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()

        if entity is None:
            return None

        return entity.to_model()

    async def list_all(self) -> list[VolunteerApplicationModel]:
        """Retrieve all volunteer applications ordered by ID (ascending)."""
        stmt = select(VolunteerApplications).order_by(VolunteerApplications.id.asc())
        result = await self.session.execute(stmt)
        entities = result.scalars().all()

        return [entity.to_model() for entity in entities]

    async def merge_role(self, *, user_id: int, new_role_model: VolunteerApplicationModel) -> None:
        """
        Merge a new-role submission into an existing volunteer application row.

        - Common fields (phone, volunteer_dates) are updated from new_role_model.
        - The role being submitted is appended to the comma-separated `function` string
          unless it's already present (overwrite case: fields updated, no duplicate).
        - All role-specific fields for the new role are written; existing role fields
          for other roles are preserved.
        """
        existing = await self.get_application(user_id=user_id)
        if existing is None:
            # No prior application — plain insert
            await self.upsert_application(model=new_role_model)
            return

        new_role = new_role_model.function or ""
        existing_roles = set(
            r.strip() for r in (existing.function or "").split(",") if r.strip()
        )

        if new_role and new_role not in existing_roles:
            existing_roles.add(new_role)

        merged_function = ",".join(sorted(existing_roles))

        # Merge: keep all previously filled fields; overlay only new-role-specific fields
        merged = VolunteerApplicationModel(
            user_id=user_id,
            # Common
            phone=new_role_model.phone or existing.phone,
            volunteer_dates=new_role_model.volunteer_dates or existing.volunteer_dates,
            function=merged_function,
            # General — keep existing unless new_role == "general"
            general_1_type=new_role_model.general_1_type if new_role == "general" else existing.general_1_type,
            general_1_answer=new_role_model.general_1_answer if new_role == "general" else existing.general_1_answer,
            general_2=new_role_model.general_2 if new_role == "general" else existing.general_2,
            general_3=new_role_model.general_3 if new_role == "general" else existing.general_3,
            general_additional_information=new_role_model.general_additional_information if new_role == "general" else existing.general_additional_information,
            # Photo — keep existing unless new_role == "photo"
            photo_portfolio=new_role_model.photo_portfolio if new_role == "photo" else existing.photo_portfolio,
            photo_has_equipment=new_role_model.photo_has_equipment if new_role == "photo" else existing.photo_has_equipment,
            photo_experience=new_role_model.photo_experience if new_role == "photo" else existing.photo_experience,
            photo_key_moments=new_role_model.photo_key_moments if new_role == "photo" else existing.photo_key_moments,
            photo_additional_information=new_role_model.photo_additional_information if new_role == "photo" else existing.photo_additional_information,
            # Translate — keep existing unless new_role == "translate"
            translate_level=new_role_model.translate_level if new_role == "translate" else existing.translate_level,
            translate_has_cert=new_role_model.translate_has_cert if new_role == "translate" else existing.translate_has_cert,
            translate_cert_link=new_role_model.translate_cert_link if new_role == "translate" else existing.translate_cert_link,
            translate_experience_detail=new_role_model.translate_experience_detail if new_role == "translate" else existing.translate_experience_detail,
            translate_worked_with_foreigners=new_role_model.translate_worked_with_foreigners if new_role == "translate" else existing.translate_worked_with_foreigners,
            translate_difficult_situation=new_role_model.translate_difficult_situation if new_role == "translate" else existing.translate_difficult_situation,
            translate_additional_information=new_role_model.translate_additional_information if new_role == "translate" else existing.translate_additional_information,
            # Legacy additional_information: keep existing
            additional_information=existing.additional_information,
            # Preserve timestamps
            id=existing.id,
            submitted_at=existing.submitted_at,
        )

        await self.upsert_application(model=merged)

        logger.info(
            "[VOLUNTEER] Role '%s' merged for user_id=%d, function now='%s'",
            new_role,
            user_id,
            merged_function,
        )
