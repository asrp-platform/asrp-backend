from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.memberships.models import MembershipRequest, MembershipType
from app.domains.users.infrastructure import UserRepository


class MembershipTypeRepository(SQLAlchemyRepository):
    model = MembershipType


class UserMembershipRepository(SQLAlchemyRepository):
    model = MembershipRequest


class MembershipsUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.membership_type_repository = MembershipTypeRepository(self._session)
        self.membership_request_repository = UserMembershipRepository(self._session)


def get_memberships_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> MembershipsUnitOfWork:
    return MembershipsUnitOfWork(session)
