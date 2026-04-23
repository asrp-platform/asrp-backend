import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.shared.transaction_managers import TransactionManager

pytestmark = pytest.mark.anyio


@pytest.fixture()
def test_transaction_manager(test_session: AsyncSession) -> TransactionManager:
    return TransactionManager(test_session)
