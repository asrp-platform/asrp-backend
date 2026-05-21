from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.memberships.models import (
    MembershipRequest,
    MembershipType,
    UserMembership,
    UserMembershipTypeChangeRequests,
)


class MembershipTypeRepository(SQLAlchemyRepository):
    model = MembershipType


class MembershipRequestsRepository(SQLAlchemyRepository):
    model = MembershipRequest


class UserMembershipRepository(SQLAlchemyRepository):
    model = UserMembership


class UserMembershipTypeChangeRequestsRepository(SQLAlchemyRepository):
    model = UserMembershipTypeChangeRequests
