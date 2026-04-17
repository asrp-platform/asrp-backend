import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure import AuthTransactionManagerBase
from app.domains.directors_board.infrastructure import DirectorsBoardMemberTransactionManagerBase
from app.domains.feedback.repositories import FeedbackTransactionManagerBase
from app.domains.memberships.repositories import MembershipsTransactionManagerBase
from app.domains.permissions.repositories import PermissionsTransactionManagerBase
from app.domains.users.infrastructure import UserTransactionManagerBase

pytestmark = pytest.mark.anyio


@pytest.fixture()
def auth_uow(test_session: AsyncSession) -> AuthTransactionManagerBase:
    return AuthTransactionManagerBase(test_session)


@pytest.fixture()
def user_uow(test_session: AsyncSession) -> UserTransactionManagerBase:
    return UserTransactionManagerBase(test_session)


@pytest.fixture()
def permissions_uow(test_session: AsyncSession) -> PermissionsTransactionManagerBase:
    return PermissionsTransactionManagerBase(test_session)


@pytest.fixture()
def directors_board_uow(test_session: AsyncSession) -> DirectorsBoardMemberTransactionManagerBase:
    return DirectorsBoardMemberTransactionManagerBase(test_session)


@pytest.fixture()
def contact_message_uow(test_session: AsyncSession) -> FeedbackTransactionManagerBase:
    return FeedbackTransactionManagerBase(test_session)


@pytest.fixture()
def membership_uow(test_session: AsyncSession) -> MembershipsTransactionManagerBase:
    return MembershipsTransactionManagerBase(test_session)
