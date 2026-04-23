from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_transaction_manager import BaseTransactionManager, SQLAlchemyTransactionManagerBase
from app.core.database.setup_db import session_getter
from app.domains.directors_board.repositories import DirectorBoardMemberRepository
from app.domains.feedback.repositories import (
    ContactMessageReplyRepository,
    ContactMessageRepository,
    FeedbackAdditionalInfoRepository,
)
from app.domains.memberships.repositories import MembershipRequestsRepository, MembershipTypeRepository
from app.domains.payments.repositories import PaymentRepository, ProcessedWebhookEventRepository
from app.domains.permissions.repositories import PermissionRepository, UserPermissionRepository
from app.domains.users.repositories import (
    CommunicationPreferencesRepository,
    FellowshipRepository,
    JobRepository,
    NameChangeRequestRepository,
    ProfessionalInformationRepository,
    ResidencyRepository,
    UserRepository,
)


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

    @property
    def contact_message_repository(self):
        return ContactMessageRepository(self._session)

    @property
    def contact_message_reply_repository(self):
        return ContactMessageReplyRepository(self._session)

    @property
    def feedback_additional_info_repository(self):
        return FeedbackAdditionalInfoRepository(self._session)

    @property
    def communication_preferences_repository(self):
        return CommunicationPreferencesRepository(self._session)

    @property
    def user_repository(self):
        return UserRepository(self._session)

    @property
    def name_change_request_repository(self):
        return NameChangeRequestRepository(self._session)

    @property
    def professional_information_repository(self):
        return ProfessionalInformationRepository(self._session)

    @property
    def residency_repository(self):
        return ResidencyRepository(self._session)

    @property
    def fellowship_repository(self):
        return FellowshipRepository(self._session)

    @property
    def job_repository(self):
        return JobRepository(self._session)

    @property
    def directors_board_member_repository(self):
        return DirectorBoardMemberRepository(self._session)


def get_transaction_manager(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> BaseTransactionManager:
    return TransactionManager(session)


TransactionManagerDep = Annotated[BaseTransactionManager, Depends(get_transaction_manager)]
