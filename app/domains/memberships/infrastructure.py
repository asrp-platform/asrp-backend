from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.base_transaction_manager import SQLAlchemyTransactionManagerBase
from app.core.database.setup_db import session_getter
from app.domains.memberships.models import MembershipRequest, MembershipType
from app.domains.users.infrastructure import UserRepository


class MembershipTypeRepository(SQLAlchemyRepository):
    model = MembershipType


class MembershipRequestsRepository(SQLAlchemyRepository):
    model = MembershipRequest


class MembershipsTransactionManagerBase(SQLAlchemyTransactionManagerBase):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.membership_type_repository = MembershipTypeRepository(self._session)
        self.membership_request_repository = MembershipRequestsRepository(self._session)


def get_memberships_unit_of_work(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> MembershipsTransactionManagerBase:
    return MembershipsTransactionManagerBase(session)
