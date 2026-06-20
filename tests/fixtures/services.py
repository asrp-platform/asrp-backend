from unittest.mock import AsyncMock

import pytest

from app.domains.emails.email_queue import EmailQueue
from app.domains.feedback.services import FeedbackAdditionalInfoService
from app.domains.memberships.services import MembershipRequestService, MembershipTypeService, UserMembershipService
from app.domains.payments.services import PaymentService
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.services import CommunicationPreferencesService, UserService


@pytest.fixture()
def membership_service(test_transaction_manager: TransactionManager):
    return MembershipRequestService(test_transaction_manager)


@pytest.fixture()
def membership_type_service(test_transaction_manager: TransactionManager):
    return MembershipTypeService(test_transaction_manager)


@pytest.fixture()
def feedback_additional_info_service(test_transaction_manager: TransactionManager):
    return FeedbackAdditionalInfoService(test_transaction_manager)


@pytest.fixture()
def communication_preference_service(test_transaction_manager: TransactionManager):
    return CommunicationPreferencesService(test_transaction_manager)


@pytest.fixture()
def payment_service(test_transaction_manager: TransactionManager):
    return PaymentService(test_transaction_manager)


@pytest.fixture()
def user_membership_service(test_transaction_manager: TransactionManager):
    return UserMembershipService(test_transaction_manager)


@pytest.fixture()
def user_service(test_transaction_manager: TransactionManager, file_storage):
    return UserService(test_transaction_manager, file_storage)


@pytest.fixture()
def email_queue():
    queue = EmailQueue()
    queue.send_email = AsyncMock()
    return queue
