import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure import AuthUnitOfWork
from app.domains.users.infrastructure import UserUnitOfWork

pytestmark = pytest.mark.anyio


@pytest.fixture()
def auth_uow(test_session: AsyncSession) -> AuthUnitOfWork:
    return AuthUnitOfWork(test_session)


@pytest.fixture()
def user_uow(test_session: AsyncSession) -> UserUnitOfWork:
    return UserUnitOfWork(test_session)
