from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_transaction_manager import BaseTransactionManager, SQLAlchemyTransactionManagerBase
from app.core.database.setup_db import session_getter
from app.domains.auth.infrastructure import UserPermissionRepository
from app.domains.memberships.infrastructure import MembershipRequestsRepository, MembershipTypeRepository
from app.domains.payments.infrastructure import PaymentRepository, ProcessedWebhookEventRepository
from app.domains.permissions.repositories import PermissionRepository


class TransactionManager(SQLAlchemyTransactionManagerBase):
    @property
    def membership_requests_repository(self):
        return MembershipRequestsRepository(self._session)

    @property
    def membership_type_repository(self):
        return MembershipTypeRepository(self._session)

    @property
    def payment_repository(self):
        return PaymentRepository(self._session)

    @property
    def processed_webhook_event_repository(self):
        return ProcessedWebhookEventRepository(self._session)

    @property
    def permission_repository(self):
        return PermissionRepository(self._session)

    @property
    def user_permission_repository(self):
        return UserPermissionRepository(self._session)


def get_transaction_manager(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> BaseTransactionManager:
    return TransactionManager(session)


TransactionManagerDep = Annotated[BaseTransactionManager, Depends(get_transaction_manager)]
