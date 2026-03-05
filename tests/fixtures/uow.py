import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure import AuthUnitOfWork
from app.domains.directors_board.infrastructure import DirectorsBoardMemberUnitOfWork
from app.domains.feedback.infrastructure import FeedbackUnitOfWork
from app.domains.memberships.infrastructure import MembershipUnitOfWork
from app.domains.permissions.infrastructure import PermissionsUnitOfWork
from app.domains.users.infrastructure import UserUnitOfWork

pytestmark = pytest.mark.anyio


@pytest.fixture()
def auth_uow(test_session: AsyncSession) -> AuthUnitOfWork:
    return AuthUnitOfWork(test_session)


@pytest.fixture()
def user_uow(test_session: AsyncSession) -> UserUnitOfWork:
    return UserUnitOfWork(test_session)


@pytest.fixture()
def permissions_uow(test_session: AsyncSession) -> PermissionsUnitOfWork:
    return PermissionsUnitOfWork(test_session)


@pytest.fixture()
def directors_board_uow(test_session: AsyncSession) -> DirectorsBoardMemberUnitOfWork:
    return DirectorsBoardMemberUnitOfWork(test_session)


@pytest.fixture()
def contact_message_uow(test_session: AsyncSession) -> FeedbackUnitOfWork:
    return FeedbackUnitOfWork(test_session)


@pytest.fixture()
def membership_uow(test_session: AsyncSession) -> MembershipUnitOfWork:
    return MembershipUnitOfWork(test_session)
