from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.memberships.models import MembershipRequest, MembershipType


class MembershipTypeRepository(SQLAlchemyRepository):
    model = MembershipType


class MembershipRequestsRepository(SQLAlchemyRepository):
    model = MembershipRequest
