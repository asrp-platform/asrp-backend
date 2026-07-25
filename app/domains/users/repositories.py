from datetime import datetime, timezone

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import selectinload

from app.core.database.base_repository import InvalidOrderAttributeError, SQLAlchemyRepository
from app.domains.memberships.models import MembershipTypeEnum, UserMembership
from app.domains.users.models import (
    CommunicationPreferences,
    Fellowship,
    Job,
    NameChangeRequest,
    ProfessionalInformation,
    Residency,
    User,
)


class UserRepository(SQLAlchemyRepository):
    model = User

    async def list_active_members(
        self,
        *,
        limit: int,
        offset: int,
        order_by: str | None = None,
        search: str | None = None,
        country: str | None = None,
        state: str | None = None,
        membership_type: MembershipTypeEnum | None = None,
    ) -> tuple[list[User], int]:
        now = datetime.now(timezone.utc)
        conditions = (
            User._deleted.is_(False),
            User.banned.is_(False),
            User.pending.is_(False),
            UserMembership._deleted.is_(False),
            UserMembership.terminated.is_(False),
            UserMembership.expires_at > now,
            or_(UserMembership.suspended_until.is_(None), UserMembership.suspended_until <= now),
        )
        stmt = (
            select(User)
            .join(UserMembership, UserMembership.user_id == User.id)
            .options(selectinload(User.membership).selectinload(UserMembership.membership_type))
            .where(*conditions)
        )
        count_stmt = (
            select(func.count(User.id)).join(UserMembership, UserMembership.user_id == User.id).where(*conditions)
        )

        if search:
            pattern = f"%{search.strip()}%"
            search_condition = or_(
                User.firstname.ilike(pattern),
                User.lastname.ilike(pattern),
                User.preferred_name.ilike(pattern),
            )
            stmt = stmt.where(search_condition)
            count_stmt = count_stmt.where(search_condition)
        if country:
            stmt = stmt.where(User.country == country)
            count_stmt = count_stmt.where(User.country == country)
        if state:
            stmt = stmt.where(User.state == state)
            count_stmt = count_stmt.where(User.state == state)
        if membership_type:
            type_condition = UserMembership.membership_type.has(type=membership_type)
            stmt = stmt.where(type_condition)
            count_stmt = count_stmt.where(type_condition)

        allowed_order_fields = {"firstname", "lastname", "country", "state", "city"}
        order_params = order_by.split(",") if order_by else ["lastname", "firstname"]
        for param in order_params:
            descending = param.startswith("-")
            field_name = param.removeprefix("-")
            if field_name not in allowed_order_fields:
                raise InvalidOrderAttributeError(f"User doesn't have an allowed member ordering field <{param}>")
            field = getattr(User, field_name)
            stmt = stmt.order_by(desc(field) if descending else asc(field))

        members = (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        count = (await self.session.execute(count_stmt)).scalar_one()
        return list(members), count


class ProfessionalInformationRepository(SQLAlchemyRepository):
    model = ProfessionalInformation


class ResidencyRepository(SQLAlchemyRepository):
    model = Residency


class FellowshipRepository(SQLAlchemyRepository):
    model = Fellowship


class JobRepository(SQLAlchemyRepository):
    model = Job


class NameChangeRequestRepository(SQLAlchemyRepository):
    model = NameChangeRequest


class CommunicationPreferencesRepository(SQLAlchemyRepository):
    model = CommunicationPreferences
