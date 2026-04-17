import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure import AuthTransactionManagerBase
from app.domains.directors_board.infrastructure import DirectorsBoardMemberTransactionManagerBase
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.infrastructure import UserTransactionManagerBase

pytestmark = pytest.mark.anyio


@pytest.fixture()
def auth_uow(test_session: AsyncSession) -> AuthTransactionManagerBase:
    return AuthTransactionManagerBase(test_session)


@pytest.fixture()
def user_uow(test_session: AsyncSession) -> UserTransactionManagerBase:
    return UserTransactionManagerBase(test_session)


@pytest.fixture()
def directors_board_uow(test_session: AsyncSession) -> DirectorsBoardMemberTransactionManagerBase:
    return DirectorsBoardMemberTransactionManagerBase(test_session)


@pytest.fixture()
def test_transaction_manager(test_session: AsyncSession) -> TransactionManager:
    return TransactionManager(test_session)
